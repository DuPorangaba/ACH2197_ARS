import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import networkx as nx
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

class StockRecommenderSystem:
    """
    Comprehensive Stock Recommender System implementing multiple approaches:
    1. Collaborative Filtering (Fund-based similarity)
    2. Content-Based Filtering (Sector/attribute-based)
    3. Co-occurrence Analysis (Market basket)
    4. Graph-Based Approach (Network analysis)
    """
    
    def __init__(self, csv_path):
        """Initialize the recommender system with data"""
        self.df = pd.read_csv(csv_path)
        self._preprocess_data()
        
    def _preprocess_data(self):
        """Clean and prepare data"""
        # Convert numeric columns
        numeric_cols = ['QT_POS_FINAL', 'VL_MERC_POS_FINAL', 
                       'QT_VENDA_NEGOC', 'VL_VENDA_NEGOC',
                       'QT_AQUIS_NEGOC', 'VL_AQUIS_NEGOC']
        
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Filter only positions with holdings
        self.holdings_df = self.df[self.df['QT_POS_FINAL'] > 0].copy()

        #Converting CNPJ to string
        self.holdings_df['CNPJ_FUNDO_CLASSE'] = self.holdings_df['CNPJ_FUNDO_CLASSE'].astype("string")
        
        # Create fund-stock matrix
        self.fund_stock_matrix = self.holdings_df.pivot_table(
            index='CNPJ_FUNDO_CLASSE',
            columns='CD_ATIVO',
            values='VL_MERC_POS_FINAL',
            fill_value=0
        )
        
        print(f"Data loaded: {len(self.holdings_df)} holdings")
        print(f"Unique funds: {self.holdings_df['CNPJ_FUNDO_CLASSE'].nunique()}")
        print(f"Unique stocks: {self.holdings_df['CD_ATIVO'].nunique()}")
    
    # ==================== APPROACH 1: COLLABORATIVE FILTERING ====================
    
    def collaborative_filtering(self, fund_cnpj, top_n=10, min_similarity=0.1):
        """
        Recommend stocks based on similar funds' holdings
        
        Args:
            fund_cnpj: Target fund identifier
            top_n: Number of recommendations
            min_similarity: Minimum similarity threshold
            
        Returns:
            DataFrame with recommended stocks and scores
        """
        print(f"\n{'='*60}")
        print("APPROACH 1: COLLABORATIVE FILTERING")
        print(f"{'='*60}")
        
        if fund_cnpj not in self.fund_stock_matrix.index:
            print(f"Fund {fund_cnpj} not found!")
            return pd.DataFrame()
        
        # Calculate cosine similarity between funds
        similarity_matrix = cosine_similarity(self.fund_stock_matrix)
        similarity_df = pd.DataFrame(
            similarity_matrix,
            index=self.fund_stock_matrix.index,
            columns=self.fund_stock_matrix.index
        )
        
        # Get similar funds
        similar_funds = similarity_df[fund_cnpj].sort_values(ascending=False)
        similar_funds = similar_funds[
            (similar_funds.index != fund_cnpj) & 
            (similar_funds > min_similarity)
        ]
        
        print(f"Found {len(similar_funds)} similar funds")
        
        # Get current holdings
        current_holdings = set(
            self.fund_stock_matrix.loc[fund_cnpj][
                self.fund_stock_matrix.loc[fund_cnpj] > 0
            ].index
        )
        
        # Calculate weighted scores for candidate stocks
        recommendations = {}
        
        for similar_fund, similarity in similar_funds.head(20).items():
            holdings = self.fund_stock_matrix.loc[similar_fund]
            holdings = holdings[holdings > 0]
            
            for stock in holdings.index:
                if stock not in current_holdings:
                    if stock not in recommendations:
                        recommendations[stock] = 0
                    recommendations[stock] += similarity
        
        # Create results DataFrame
        if recommendations:
            results = pd.DataFrame([
                {
                    'stock': stock,
                    'score': score,
                    'similar_funds_holding': sum(
                        1 for f in similar_funds.head(20).index 
                        if self.fund_stock_matrix.loc[f, stock] > 0
                    )
                }
                for stock, score in recommendations.items()
            ]).sort_values('score', ascending=False).head(top_n)
            
            # Add stock details
            results = self._add_stock_details(results)
            
            print(f"\nTop {len(results)} recommendations:")
            print(results[['stock', 'name', 'sector', 'score']].to_string(index=False))
            
            return results
        
        return pd.DataFrame()
    
    # ==================== APPROACH 2: CONTENT-BASED FILTERING ====================
    
    def content_based_filtering(self, fund_cnpj, top_n=10):
        """
        Recommend stocks based on fund's sector preferences and characteristics
        
        Args:
            fund_cnpj: Target fund identifier
            top_n: Number of recommendations
            
        Returns:
            DataFrame with recommended stocks and scores
        """
        print(f"\n{'='*60}")
        print("APPROACH 2: CONTENT-BASED FILTERING")
        print(f"{'='*60}")
        
        # Get fund's current holdings
        fund_holdings = self.holdings_df[
            self.holdings_df['CNPJ_FUNDO_CLASSE'] == fund_cnpj
        ].copy()
        
        if len(fund_holdings) == 0:
            print(f"Fund {fund_cnpj} not found!")
            return pd.DataFrame()
        
        # Calculate sector distribution
        sector_weights = fund_holdings.groupby('Setor')['VL_MERC_POS_FINAL'].sum()
        sector_weights = sector_weights / sector_weights.sum()
        
        print(f"\nFund's sector profile:")
        for sector, weight in sector_weights.head(5).items():
            print(f"  {sector}: {weight:.1%}")
        
        # Get stocks not currently held
        current_stocks = set(fund_holdings['CD_ATIVO'])
        candidate_stocks = self.holdings_df[
            ~self.holdings_df['CD_ATIVO'].isin(current_stocks)
        ].copy()
        
        # Score candidates based on sector match
        candidate_stocks['sector_score'] = candidate_stocks['Setor'].map(
            sector_weights
        ).fillna(0)
        
        # Calculate popularity (how many funds hold it)
        stock_popularity = self.holdings_df.groupby('CD_ATIVO').size()
        candidate_stocks['popularity'] = candidate_stocks['CD_ATIVO'].map(
            stock_popularity
        )
        
        # Normalize and combine scores
        max_popularity = candidate_stocks['popularity'].max()
        candidate_stocks['popularity_norm'] = (
            candidate_stocks['popularity'] / max_popularity
        )
        
        candidate_stocks['score'] = (
            0.7 * candidate_stocks['sector_score'] + 
            0.3 * candidate_stocks['popularity_norm']
        )
        
        # Get top recommendations
        results = candidate_stocks.groupby('CD_ATIVO').agg({
            'DS_ATIVO': 'first',
            'Setor': 'first',
            'score': 'max',
            'popularity': 'first'
        }).reset_index()
        
        results.columns = ['stock', 'name', 'sector', 'score', 'popularity']
        results = results.sort_values('score', ascending=False).head(top_n)
        
        print(f"\nTop {len(results)} recommendations:")
        print(results[['stock', 'name', 'sector', 'score']].to_string(index=False))
        
        return results
    
    # ==================== APPROACH 3: CO-OCCURRENCE ANALYSIS ====================
    
    def cooccurrence_analysis(self, fund_cnpj, top_n=10, min_cooccurrence=2):
        """
        Recommend stocks that frequently co-occur with fund's holdings
        (Market basket analysis)
        
        Args:
            fund_cnpj: Target fund identifier
            top_n: Number of recommendations
            min_cooccurrence: Minimum co-occurrence threshold
            
        Returns:
            DataFrame with recommended stocks and scores
        """
        print(f"\n{'='*60}")
        print("APPROACH 3: CO-OCCURRENCE ANALYSIS")
        print(f"{'='*60}")
        
        # Get fund's current holdings
        fund_holdings = self.holdings_df[
            self.holdings_df['CNPJ_FUNDO_CLASSE'] == fund_cnpj
        ]['CD_ATIVO'].unique()
        
        if len(fund_holdings) == 0:
            print(f"Fund {fund_cnpj} not found!")
            return pd.DataFrame()
        
        print(f"Analyzing co-occurrence patterns for {len(fund_holdings)} stocks")
        
        # Build co-occurrence matrix
        cooccurrence = defaultdict(lambda: defaultdict(int))
        
        # For each fund, count which stocks appear together
        for fund in self.holdings_df['CNPJ_FUNDO_CLASSE'].unique():
            stocks = set(self.holdings_df[
                self.holdings_df['CNPJ_FUNDO_CLASSE'] == fund
            ]['CD_ATIVO'])
            
            # Count co-occurrences
            for stock1 in stocks:
                for stock2 in stocks:
                    if stock1 != stock2:
                        cooccurrence[stock1][stock2] += 1
        
        # Calculate scores for candidate stocks
        recommendations = defaultdict(float)
        
        for held_stock in fund_holdings:
            if held_stock in cooccurrence:
                for candidate_stock, count in cooccurrence[held_stock].items():
                    if candidate_stock not in fund_holdings:
                        # Use lift-like measure
                        total_funds = self.holdings_df['CNPJ_FUNDO_CLASSE'].nunique()
                        support_held = self.holdings_df[
                            self.holdings_df['CD_ATIVO'] == held_stock
                        ]['CNPJ_FUNDO_CLASSE'].nunique()
                        support_candidate = self.holdings_df[
                            self.holdings_df['CD_ATIVO'] == candidate_stock
                        ]['CNPJ_FUNDO_CLASSE'].nunique()
                        
                        expected = (support_held * support_candidate) / total_funds
                        lift = count / expected if expected > 0 else 0
                        
                        recommendations[candidate_stock] += lift
        
        # Create results DataFrame
        if recommendations:
            results = pd.DataFrame([
                {
                    'stock': stock,
                    'score': score,
                    'cooccurrence_count': sum(
                        cooccurrence[held][stock] 
                        for held in fund_holdings 
                        if stock in cooccurrence[held]
                    )
                }
                for stock, score in recommendations.items()
                if sum(cooccurrence[held][stock] for held in fund_holdings 
                      if stock in cooccurrence[held]) >= min_cooccurrence
            ]).sort_values('score', ascending=False).head(top_n)
            
            # Add stock details
            results = self._add_stock_details(results)
            
            print(f"\nTop {len(results)} recommendations:")
            print(results[['stock', 'name', 'sector', 'score']].to_string(index=False))
            
            return results
        
        return pd.DataFrame()
    
    # ==================== APPROACH 4: GRAPH-BASED APPROACH ====================
    
    def graph_based_recommendation(self, fund_cnpj, top_n=10):
        """
        Recommend stocks using graph analysis (bipartite fund-stock network)
        
        Args:
            fund_cnpj: Target fund identifier
            top_n: Number of recommendations
            
        Returns:
            DataFrame with recommended stocks and scores
        """
        print(f"\n{'='*60}")
        print("APPROACH 4: GRAPH-BASED APPROACH")
        print(f"{'='*60}")
        
        # Create bipartite graph
        G = nx.Graph()
        
        # Add nodes
        funds = self.holdings_df['CNPJ_FUNDO_CLASSE'].unique()
        stocks = self.holdings_df['CD_ATIVO'].unique()
        
        G.add_nodes_from(funds, bipartite=0)
        G.add_nodes_from(stocks, bipartite=1)
        
        # Add edges (fund-stock relationships)
        for _, row in self.holdings_df.iterrows():
            # Weight by position value
            weight = np.log1p(row['VL_MERC_POS_FINAL'])
            G.add_edge(
                row['CNPJ_FUNDO_CLASSE'], 
                row['CD_ATIVO'],
                weight=weight
            )
        
        print(f"Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Get fund's current holdings
        fund_holdings = set(self.holdings_df[
            self.holdings_df['CNPJ_FUNDO_CLASSE'] == fund_cnpj
        ]['CD_ATIVO'])
        
        if fund_cnpj not in G:
            print(f"Fund {fund_cnpj} not found!")
            return pd.DataFrame()
        
        # Calculate PageRank-like scores
        pagerank = nx.pagerank(G, weight='weight')
        
        # Alternative: Use random walk with restart from fund node
        recommendations = {}
        
        # Find stocks connected through similar funds
        fund_neighbors = list(G.neighbors(fund_cnpj))  # Stocks held by fund
        
        for stock in fund_neighbors:
            # Get funds that also hold this stock
            stock_neighbors = [n for n in G.neighbors(stock) if n in funds]
            
            # For each similar fund, get their other holdings
            for similar_fund in stock_neighbors:
                if similar_fund != fund_cnpj:
                    for candidate_stock in G.neighbors(similar_fund):
                        if candidate_stock in stocks and candidate_stock not in fund_holdings:
                            # Score based on connection strength
                            if candidate_stock not in recommendations:
                                recommendations[candidate_stock] = {
                                    'score': 0,
                                    'path_count': 0
                                }
                            
                            # Weight by edge weights
                            weight = (
                                G[fund_cnpj][stock]['weight'] *
                                G[similar_fund][candidate_stock]['weight']
                            )
                            
                            recommendations[candidate_stock]['score'] += weight
                            recommendations[candidate_stock]['path_count'] += 1
        
        # Also consider PageRank scores
        for stock in stocks:
            if stock not in fund_holdings and stock in pagerank:
                if stock not in recommendations:
                    recommendations[stock] = {
                        'score': 0,
                        'path_count': 0
                    }
                recommendations[stock]['score'] += pagerank[stock] * 100
        
        # Create results DataFrame
        if recommendations:
            results = pd.DataFrame([
                {
                    'stock': stock,
                    'score': data['score'],
                    'path_count': data['path_count'],
                    'pagerank': pagerank.get(stock, 0)
                }
                for stock, data in recommendations.items()
            ]).sort_values('score', ascending=False).head(top_n)
            
            # Add stock details
            results = self._add_stock_details(results)
            
            print(f"\nTop {len(results)} recommendations:")
            print(results[['stock', 'name', 'sector', 'score']].to_string(index=False))
            
            return results
        
        return pd.DataFrame()
    
    def graph_based_recommendation_v2(self, fund_cnpj, top_n=10):
        """
        Recommend stocks using graph analysis with buy/sell signals
        
        Creates a signed network where:
        - Positive edges (green): Purchases (QT_AQUIS_NEGOC > 0) = Bullish signal
        - Negative edges (red): Sales (QT_VENDA_NEGOC > 0) = Bearish signal
        
        Logic: If similar funds are BUYING a stock (positive sentiment), 
               recommend it. If they're SELLING, avoid it.
        
        Args:
            fund_cnpj: Target fund identifier
            top_n: Number of recommendations
            
        Returns:
            DataFrame with recommended stocks and scores
        """
        print(f"\n{'='*60}")
        print("APPROACH 4: GRAPH-BASED APPROACH (Buy/Sell Signals)")
        print(f"{'='*60}")
        
        # Create SIGNED directed graph
        G = nx.DiGraph()
        
        # Add nodes
        funds = self.df['CNPJ_FUNDO_CLASSE'].unique().astype("str")
        stocks = self.df['CD_ATIVO'].unique().astype("str")
        
        G.add_nodes_from(funds, bipartite=0, node_type='fund')
        G.add_nodes_from(stocks, bipartite=1, node_type='stock')
        
        # Track sentiment statistics
        buy_signals = 0
        sell_signals = 0
        neutral_signals = 0
        
        # Add edges based on buy/sell activity
        for _, row in self.df.iterrows():
            fund = row['CNPJ_FUNDO_CLASSE']
            stock = row['CD_ATIVO']
            
            qty_bought = row['QT_AQUIS_NEGOC']
            qty_sold = row['QT_VENDA_NEGOC']
            val_bought = row['VL_AQUIS_NEGOC']
            val_sold = row['VL_VENDA_NEGOC']
            
            # Calculate net sentiment
            # Positive = buying, Negative = selling
            net_quantity = qty_bought - qty_sold
            net_value = val_bought - val_sold
            
            if net_value != 0:  # There was trading activity
                # Create edge with signed weight
                # Positive weight = bullish (buying)
                # Negative weight = bearish (selling)
                
                # Use log transform to normalize large values
                if net_value > 0:
                    weight = np.log1p(abs(net_value))
                    sentiment = 'buy'
                    buy_signals += 1
                else:
                    weight = -np.log1p(abs(net_value))
                    sentiment = 'sell'
                    sell_signals += 1
                
                G.add_edge(
                    fund,
                    stock,
                    weight=weight,
                    sentiment=sentiment,
                    net_value=net_value,
                    net_quantity=net_quantity
                )
            elif row['QT_POS_FINAL'] > 0:
                # Holding but no activity = neutral
                neutral_signals += 1
        
        print(f"Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Buy signals (positive edges): {buy_signals}")
        print(f"Sell signals (negative edges): {sell_signals}")
        print(f"Holdings with no activity: {neutral_signals}")
        
        # Get fund's current holdings and activity
        fund_data = self.df[self.df['CNPJ_FUNDO_CLASSE'].astype("string") == fund_cnpj]
        
        if len(fund_data) == 0 or fund_cnpj not in G:
            print(f"Fund {fund_cnpj} not found!")
            return pd.DataFrame()
        
        # Get stocks currently held by the fund
        current_holdings = set(fund_data[
            fund_data['QT_POS_FINAL'] > 0
        ]['CD_ATIVO'])
        
        print(f"\nAnalyzing trading patterns from {len(current_holdings)} held stocks")
        
        # Calculate stock sentiment scores
        recommendations = {}
        
        # Method 1: Direct sentiment aggregation
        # For each stock, aggregate sentiment from all funds
        for stock in stocks:
            if stock not in current_holdings:
                # Get all edges pointing to this stock
                in_edges = G.in_edges(stock, data=True)
                
                total_sentiment = 0
                buy_count = 0
                sell_count = 0
                total_volume = 0
                
                for fund, _, edge_data in in_edges:
                    weight = edge_data['weight']
                    total_sentiment += weight
                    total_volume += abs(edge_data['net_value'])
                    
                    if edge_data['sentiment'] == 'buy':
                        buy_count += 1
                    else:
                        sell_count += 1
                
                # Calculate metrics
                if buy_count + sell_count > 0:
                    buy_ratio = buy_count / (buy_count + sell_count)
                    
                    recommendations[stock] = {
                        'sentiment_score': total_sentiment,
                        'buy_count': buy_count,
                        'sell_count': sell_count,
                        'buy_ratio': buy_ratio,
                        'net_signal': buy_count - sell_count,
                        'total_volume': total_volume,
                        'activity_score': buy_count + sell_count
                    }
        
        # Method 2: Similar funds analysis
        # Find funds similar to target fund based on overlapping positions
        fund_similarity = {}
        
        for other_fund in funds:
            if other_fund != fund_cnpj:
                # Calculate Jaccard similarity based on held stocks
                other_holdings = set(self.df[
                    (self.df['CNPJ_FUNDO_CLASSE'] == other_fund) &
                    (self.df['QT_POS_FINAL'] > 0)
                ]['CD_ATIVO'])
                
                if len(other_holdings) > 0:
                    intersection = len(current_holdings & other_holdings)
                    union = len(current_holdings | other_holdings)
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.05:  # At least 5% overlap
                        fund_similarity[other_fund] = similarity
        
        print(f"Found {len(fund_similarity)} similar funds")
        
        # Method 3: Weighted recommendations from similar funds
        for stock in recommendations.keys():
            weighted_sentiment = 0
            
            # Get sentiment from similar funds
            for similar_fund, similarity in fund_similarity.items():
                if G.has_edge(similar_fund, stock):
                    edge_data = G[similar_fund][stock]
                    # Weight by fund similarity
                    weighted_sentiment += edge_data['weight'] * similarity
            
            recommendations[stock]['weighted_sentiment'] = weighted_sentiment
        
        # Calculate final score combining multiple factors
        for stock in recommendations.keys():
            rec = recommendations[stock]
            
            # Normalize components
            max_activity = max([r['activity_score'] for r in recommendations.values()]) or 1
            
            # Final score combines:
            # 1. Overall market sentiment (40%)
            # 2. Similar funds' sentiment (30%)
            # 3. Buy ratio (20%)
            # 4. Trading activity level (10%)
            
            score = (
                0.40 * rec['sentiment_score'] +
                0.30 * rec['weighted_sentiment'] +
                0.20 * rec['buy_ratio'] * 10 +  # Scale to comparable range
                0.10 * (rec['activity_score'] / max_activity) * 10
            )
            
            recommendations[stock]['final_score'] = score
        
        # Create results DataFrame
        if recommendations:
            results = pd.DataFrame([
                {
                    'stock': stock,
                    'score': data['final_score'],
                    'sentiment_score': data['sentiment_score'],
                    'buy_count': data['buy_count'],
                    'sell_count': data['sell_count'],
                    'buy_ratio': data['buy_ratio'],
                    'net_signal': data['net_signal'],
                    'weighted_sentiment': data['weighted_sentiment']
                }
                for stock, data in recommendations.items()
            ])
            
            # Filter for positive sentiment
            results = results[results['score'] > 0].sort_values('score', ascending=False).head(top_n)
            
            # Add stock details
            results = self._add_stock_details(results)
            
            print(f"\nTop {len(results)} recommendations (positive sentiment):")
            if len(results) > 0:
                print(results[[
                    'stock', 'name', 'sector', 'score', 
                    'buy_count', 'sell_count', 'buy_ratio'
                ]].to_string(index=False))
            else:
                print("No stocks with positive net sentiment found.")
            
            return results
        
        return pd.DataFrame()
 
 
    # ==================== ENSEMBLE METHOD ====================
    
    def ensemble_recommendation(self, fund_cnpj, top_n=10):
        """
        Combine all approaches using ensemble method
        
        Args:
            fund_cnpj: Target fund identifier
            top_n: Number of recommendations
            
        Returns:
            DataFrame with recommended stocks and combined scores
        """
        print(f"\n{'='*60}")
        print("ENSEMBLE METHOD (Combining All Approaches)")
        print(f"{'='*60}")
        
        # Get recommendations from each approach
        cf_rec = self.collaborative_filtering(fund_cnpj, top_n=20)
        cb_rec = self.content_based_filtering(fund_cnpj, top_n=20)
        co_rec = self.cooccurrence_analysis(fund_cnpj, top_n=20)
        gb_rec = self.graph_based_recommendation_v2(fund_cnpj, top_n=20)
        
        # Normalize scores
        def normalize_scores(df):
            if len(df) > 0 and 'score' in df.columns:
                df = df.copy()
                max_score = df['score'].max()
                if max_score > 0:
                    df['score'] = df['score'] / max_score
            return df
        
        cf_rec = normalize_scores(cf_rec)
        cb_rec = normalize_scores(cb_rec)
        co_rec = normalize_scores(co_rec)
        gb_rec = normalize_scores(gb_rec)
        
        # Combine recommendations
        all_stocks = set()
        if len(cf_rec) > 0:
            all_stocks.update(cf_rec['stock'])
        if len(cb_rec) > 0:
            all_stocks.update(cb_rec['stock'])
        if len(co_rec) > 0:
            all_stocks.update(co_rec['stock'])
        if len(gb_rec) > 0:
            all_stocks.update(gb_rec['stock'])
        
        # Calculate weighted ensemble score
        ensemble_results = []
        
        for stock in all_stocks:
            scores = {}
            
            if len(cf_rec) > 0:
                cf_score = cf_rec[cf_rec['stock'] == stock]['score'].values
                scores['collaborative'] = cf_score[0] if len(cf_score) > 0 else 0
            else:
                scores['collaborative'] = 0
                
            if len(cb_rec) > 0:
                cb_score = cb_rec[cb_rec['stock'] == stock]['score'].values
                scores['content'] = cb_score[0] if len(cb_score) > 0 else 0
            else:
                scores['content'] = 0
                
            if len(co_rec) > 0:
                co_score = co_rec[co_rec['stock'] == stock]['score'].values
                scores['cooccurrence'] = co_score[0] if len(co_score) > 0 else 0
            else:
                scores['cooccurrence'] = 0
                
            if len(gb_rec) > 0:
                gb_score = gb_rec[gb_rec['stock'] == stock]['score'].values
                scores['graph'] = gb_score[0] if len(gb_score) > 0 else 0
            else:
                scores['graph'] = 0
            
            # Weighted combination (can be tuned)
            ensemble_score = (
                0.3 * scores['collaborative'] +
                0.25 * scores['content'] +
                0.25 * scores['cooccurrence'] +
                0.2 * scores['graph']
            )
            
            ensemble_results.append({
                'stock': stock,
                'ensemble_score': ensemble_score,
                'cf_score': scores['collaborative'],
                'cb_score': scores['content'],
                'co_score': scores['cooccurrence'],
                'gb_score': scores['graph'],
                'num_methods': sum(1 for s in scores.values() if s > 0)
            })
        
        results = pd.DataFrame(ensemble_results)
        results = results.sort_values('ensemble_score', ascending=False).head(top_n)
        
        # Add stock details
        results = self._add_stock_details(results)
        
        print(f"\n{'='*60}")
        print(f"FINAL ENSEMBLE RECOMMENDATIONS")
        print(f"{'='*60}")
        print(results[['stock', 'name', 'sector', 'ensemble_score', 'num_methods']].to_string(index=False))
        
        return results
    
    # ==================== HELPER METHODS ====================
    
    def _add_stock_details(self, df):
        """Add stock name and sector to results DataFrame"""
        if len(df) > 0 and 'stock' in df.columns:
            stock_info = self.holdings_df[['CD_ATIVO', 'DS_ATIVO', 'Setor']].drop_duplicates()
            stock_info.columns = ['stock', 'name', 'sector']
            df = df.merge(stock_info, on='stock', how='left')
        return df
    
    def get_fund_profile(self, fund_cnpj):
        """Get detailed profile of a fund"""
        fund_data = self.holdings_df[
            self.holdings_df['CNPJ_FUNDO_CLASSE'] == fund_cnpj
        ]
        
        if len(fund_data) == 0:
            print(f"Fund {fund_cnpj} not found!")
            return
        
        print(f"\n{'='*60}")
        print(f"FUND PROFILE: {fund_data['DENOM_SOCIAL'].iloc[0][:60]}")
        print(f"{'='*60}")
        
        print(f"\nTotal holdings: {len(fund_data)}")
        print(f"Total market value: R$ {fund_data['VL_MERC_POS_FINAL'].sum():,.2f}")
        
        print(f"\nSector distribution:")
        sector_dist = fund_data.groupby('Setor')['VL_MERC_POS_FINAL'].sum()
        sector_dist = sector_dist.sort_values(ascending=False)
        for sector, value in sector_dist.items():
            pct = value / sector_dist.sum() * 100
            print(f"  {sector:30s}: {pct:5.1f}%")
        
        print(f"\nTop 10 holdings:")
        top_holdings = fund_data.nlargest(10, 'VL_MERC_POS_FINAL')
        for _, row in top_holdings.iterrows():
            pct = row['VL_MERC_POS_FINAL'] / fund_data['VL_MERC_POS_FINAL'].sum() * 100
            print(f"  {row['CD_ATIVO']:8s} - {row['DS_ATIVO'][:40]:40s}: {pct:5.1f}%")


# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    # Initialize recommender system
    print("Loading Stock Recommender System...")
    ARQUIVO_ENTRADA = '../../output/carteiras_com_setores_202406_amostra.csv'
    recommender = StockRecommenderSystem(ARQUIVO_ENTRADA)
    
    # Select a fund for analysis
    # Let's use one of the larger funds
    target_fund = '2661252000197'  # FAPI AGGRESSIVE IB MULTIMERCADO
    
    # Get fund profile
    recommender.get_fund_profile(target_fund)
    
    # Apply each recommendation approach
    print(f"\n\n{'#'*60}")
    print("GENERATING RECOMMENDATIONS FOR FUND")
    print(f"{'#'*60}")
    
    # 1. Collaborative Filtering
    cf_recommendations = recommender.collaborative_filtering(target_fund, top_n=10)
    
    # 2. Content-Based Filtering
    cb_recommendations = recommender.content_based_filtering(target_fund, top_n=10)
    
    # 3. Co-occurrence Analysis
    co_recommendations = recommender.cooccurrence_analysis(target_fund, top_n=10)
    
    # 4. Graph-Based Approach
    gb_recommendations = recommender.graph_based_recommendation(target_fund, top_n=10)

        # 4. Graph-Based Approach
    gb_recommendations = recommender.graph_based_recommendation_v2(target_fund, top_n=10)
    
    # 5. Ensemble Method
    ensemble_recommendations = recommender.ensemble_recommendation(target_fund, top_n=15)
    
    print(f"\n{'='*60}")
    print("RECOMMENDATION SYSTEM COMPLETE")
    print(f"{'='*60}")