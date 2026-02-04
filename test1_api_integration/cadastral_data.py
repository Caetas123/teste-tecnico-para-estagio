import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Optional

class CadastralDataFetcher:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.base_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
        self.cadastral_file = data_dir / "operadoras_cadastro.csv"
    
    def download_cadastral_data(self) -> Optional[pd.DataFrame]:
        if self.cadastral_file.exists():
            print("Dados cadastrais já existem, carregando...")
            return pd.read_csv(self.cadastral_file, sep=';', encoding='latin1', low_memory=False)
        
        print("Baixando dados cadastrais das operadoras...")
        try:
            response = requests.get(self.base_url)
            if response.status_code != 200:
                print(f"Erro ao acessar cadastro: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            csv_links = []
            
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.csv'):
                    csv_links.append(href)
            
            if not csv_links:
                print("Nenhum arquivo CSV encontrado no cadastro")
                return None
            
            csv_url = self.base_url + csv_links[0]
            print(f"Baixando: {csv_url}")
            
            df = pd.read_csv(csv_url, sep=';', encoding='latin1', low_memory=False)
            df.to_csv(self.cadastral_file, sep=';', encoding='latin1', index=False)
            
            print(f"Dados cadastrais salvos: {len(df)} operadoras")
            return df
            
        except Exception as e:
            print(f"Erro ao baixar dados cadastrais: {e}")
            return None
    
    def map_reg_ans_to_cnpj(self, df: pd.DataFrame, cadastral_df: pd.DataFrame) -> pd.DataFrame:
        print("Mapeando REG_ANS para CNPJ e RazaoSocial...")
        
        cadastral_df.columns = cadastral_df.columns.str.strip().str.upper()
        
        reg_ans_col = None
        for col in cadastral_df.columns:
            if ('REGISTRO' in col and 'OPERADORA' in col) or ('REGISTRO' in col and 'ANS' in col):
                reg_ans_col = col
                break
        
        cnpj_col = None
        for col in cadastral_df.columns:
            if 'CNPJ' in col:
                cnpj_col = col
                break
        
        razao_col = None
        for col in cadastral_df.columns:
            if 'RAZAO' in col or ('SOCIAL' in col and 'RAZAO' not in col):
                razao_col = col
                break
        
        if not reg_ans_col or not cnpj_col:
            print("Colunas necessárias não encontradas no cadastro")
            print(f"Colunas disponíveis: {list(cadastral_df.columns)}")
            df['CNPJ'] = df['REG_ANS'].astype(str)
            df['RazaoSocial'] = ''
            return df
        
        cols_to_select = [reg_ans_col, cnpj_col]
        if razao_col:
            cols_to_select.append(razao_col)
        
        cadastral_mapping = cadastral_df[cols_to_select].copy()
        cadastral_mapping = cadastral_mapping.drop_duplicates(subset=[reg_ans_col])
        
        if razao_col:
            cadastral_mapping.columns = ['REG_ANS', 'CNPJ', 'RazaoSocial']
        else:
            cadastral_mapping.columns = ['REG_ANS', 'CNPJ']
            cadastral_mapping['RazaoSocial'] = ''
        
        df['REG_ANS'] = df['REG_ANS'].astype(str).str.strip()
        cadastral_mapping['REG_ANS'] = cadastral_mapping['REG_ANS'].astype(str).str.strip()
        cadastral_mapping['CNPJ'] = cadastral_mapping['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
        
        merged = df.merge(cadastral_mapping, on='REG_ANS', how='left', suffixes=('_old', ''))
        
        # Identificar CNPJs duplicados com razões sociais diferentes
        duplicates = merged[merged.duplicated(subset=['CNPJ'], keep=False)]
        if not duplicates.empty:
            cnpj_groups = duplicates.groupby('CNPJ')['RazaoSocial'].unique()
            conflicting = cnpj_groups[cnpj_groups.apply(len) > 1]
            if len(conflicting) > 0:
                print(f"AVISO: {len(conflicting)} CNPJs com múltiplas razões sociais (mantendo a mais recente)")
        
        merged['CNPJ'] = merged['CNPJ'].fillna(merged['REG_ANS'])
        merged['RazaoSocial'] = merged['RazaoSocial'].fillna('')
        
        if 'CNPJ_old' in merged.columns:
            merged = merged.drop(columns=['CNPJ_old'])
        if 'RazaoSocial_old' in merged.columns:
            merged = merged.drop(columns=['RazaoSocial_old'])
        
        matches = (merged['RazaoSocial'] != '').sum()
        print(f"Mapeados com sucesso: {matches}/{len(df)} registros")
        
        return merged
