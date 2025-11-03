import pandas as pd
import sys
import datetime
import os
import glob
import re

sys.path.insert(0, "/home/duda/Documentos/USP/8semestre/ars/ACH2197_ARS/src")
from cvm_data.script.main import cvm_data_limpeza
from yahoo_data.script.main import yahoo_data
from merge_data.script.merge import merge_data 
from graph.script.graph_transactions import create_transaction_graph
from graph.script.graph_setor import create_graph

# --- 1. Configurações ---
ARQUIVOS_CARTEIRAS = os.path.join(os.path.dirname(__file__), "cvm_data", "input")


def get_period_from_filename(filename: str) -> str:
    """Extract period from filename."""
    match = re.search(r'_(\d{6})\.', filename)
    if match:
        return match.group(1)
    return None

def check_output_exists(periodo: str, step: str) -> bool:
    """Check if output file exists for given step."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    paths = {
        'cvm': os.path.join(base_dir, "src", "cvm_data", "output", f"carteiras_acoes_limpo_{periodo}.csv"),
        'yahoo': os.path.join(base_dir, "src", "yahoo_data", "output", f"ativo_setores-{periodo}.csv"),
        'merge': os.path.join(base_dir, "src", "output", f"carteiras_com_setores_{periodo}.csv"),
        'graph_trans': os.path.join(base_dir, "src", "graph", "output", f"rede_dirigida_fundo_ativo_{periodo}.graphml"),
        'graph_setor': os.path.join(base_dir, "src", "graph", "output", f"rede_dirigida_fundo_setor_{periodo}.graphml")
    }
    file_path = paths.get(step, '')
    exists = os.path.exists(file_path)
    
    return exists
    

def process_files():
    """Process all files in the input directory."""
    # Get all CSV files from input directory
    input_files = glob.glob(os.path.join(ARQUIVOS_CARTEIRAS, "*.csv"))
    print(input_files)
    if not input_files:
        print("❌ No CSV files found in input directory!")
        return
    
    print(f"🔍 Found {len(input_files)} files to process")
    
    for input_file in input_files:
        print(f"\n📁 Processing file: {input_file}")
        
        # Get period from filename
        periodo = get_period_from_filename(input_file)
        if not periodo:
            print(f"❌ Could not extract period from filename: {input_file}")
            return
            
        try:
            # 1. Process CVM data
            if check_output_exists(periodo, 'cvm'):
                print("✅ CVM data already processed, skipping...")
            else:
                print("\n=== Running CVM data processing ===")
                df_cvm = cvm_data_limpeza(input_file)
                if df_cvm is None or df_cvm.empty:
                    print("❌ CVM data processing failed")
                    return
                
            # 2. Process Yahoo data
            if check_output_exists(periodo, 'yahoo'):
                print("✅ Yahoo data already processed, skipping...")
            else:
                print("\n=== Running Yahoo data processing ===")
                df_yahoo = yahoo_data(periodo)
                if df_yahoo is None or df_yahoo.empty:
                    print("❌ Yahoo data processing failed")
                    return
                
            # 3. Merge data
            if check_output_exists(periodo, 'merge'):
                print("✅ Merge already processed, skipping...")
            else:
                print("\n=== Running data merge ===")
                df_merged = merge_data(periodo)
                if df_merged is None or df_merged.empty:
                    print("❌ Data merge failed")
                    return
                
             # 4. Graph Transactions
            if check_output_exists(periodo, 'graph_trans'):
                print("✅ Graph transactions already processed, skipping...")
            else:
                print("\n=== Running graph transactions processing ===")
                G_trans = create_transaction_graph(periodo)
                if G_trans is None:
                    print("❌ Graph transactions processing failed")
                    return
                
            # 5. Graph Sector
            if check_output_exists(periodo, 'graph_setor'):
                print("✅ Graph sector already processed, skipping...")
            else:
                print("\n=== Running graph sector processing ===")
                G_setor = create_graph(periodo)
                if G_setor is None:
                    print("❌ Graph sector processing failed")
                    return
                
            print(f"✅ Successfully processed file for period {periodo}")
            
        except Exception as e:
            print(f"❌ Error processing file {input_file}: {str(e)}")
            continue

if __name__ == "__main__":
    print("🚀 Starting data processing pipeline...")
    process_files()
    print("\n✨ Processing complete!")



