import pandas as pd
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from config.settings import ANS_OPERADORAS_URL, REQUEST_TIMEOUT

class DataEnrichment:
    def __init__(self):
        self.enrichment_log = []
    
    def download_operadoras_data(self, data_dir: Path) -> Path:
        print("Baixando dados cadastrais das operadoras para campos adicionais...")
        
        try:
            response = requests.get(ANS_OPERADORAS_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            csv_files = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href.endswith('.csv'):
                    csv_files.append(ANS_OPERADORAS_URL + href)
            
            if not csv_files:
                raise ValueError("Nenhum arquivo CSV encontrado")
            
            file_url = csv_files[0]
            print(f"Baixando: {file_url}")
            
            response = requests.get(file_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            output_path = data_dir / 'operadoras_ativas.csv'
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Arquivo salvo: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erro ao baixar dados cadastrais: {e}")
            raise
    
    def load_operadoras_data(self, file_path: Path) -> pd.DataFrame:
        print("Carregando dados cadastrais...")
        
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
            for sep in [';', ',', '|']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=sep, low_memory=False)
                    if len(df.columns) > 1:
                        print(f"Arquivo carregado: {len(df)} registros")
                        return df
                except:
                    continue
        
        raise ValueError("Não foi possível ler o arquivo de operadoras")
    
    def enrich_with_additional_fields(self, despesas_df: pd.DataFrame, operadoras_df: pd.DataFrame) -> pd.DataFrame:
        print("Adicionando campos adicionais: RegistroANS, Modalidade, UF...")
        
        operadoras_df.columns = operadoras_df.columns.str.strip().str.upper()
        
        cnpj_col = [col for col in operadoras_df.columns if 'CNPJ' in col][0]
        registro_cols = [col for col in operadoras_df.columns if 'REGISTRO' in col or 'ANS' in col]
        modalidade_cols = [col for col in operadoras_df.columns if 'MODALIDADE' in col]
        uf_cols = [col for col in operadoras_df.columns if 'UF' in col or 'ESTADO' in col]
        
        operadoras_clean = operadoras_df.copy()
        operadoras_clean['CNPJ'] = operadoras_clean[cnpj_col].astype(str).str.replace(r'\D', '', regex=True)
        
        operadoras_clean = operadoras_clean.rename(columns={
            registro_cols[0] if registro_cols else cnpj_col: 'RegistroANS',
            modalidade_cols[0] if modalidade_cols else cnpj_col: 'Modalidade',
            uf_cols[0] if uf_cols else cnpj_col: 'UF'
        })
        
        if 'RegistroANS' not in operadoras_clean.columns:
            operadoras_clean['RegistroANS'] = ''
        if 'Modalidade' not in operadoras_clean.columns:
            operadoras_clean['Modalidade'] = ''
        if 'UF' not in operadoras_clean.columns:
            operadoras_clean['UF'] = ''
        
        operadoras_clean = operadoras_clean[['CNPJ', 'RegistroANS', 'Modalidade', 'UF']]
        
        duplicates = operadoras_clean[operadoras_clean.duplicated(subset=['CNPJ'], keep=False)]
        if not duplicates.empty:
            print(f"Encontrados {duplicates['CNPJ'].nunique()} CNPJs duplicados no cadastro")
            operadoras_clean = operadoras_clean.drop_duplicates(subset=['CNPJ'], keep='first')
        
        despesas_df['CNPJ'] = despesas_df['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
        
        enriched_df = despesas_df.merge(
            operadoras_clean,
            on='CNPJ',
            how='left',
            indicator=True
        )
        
        no_match = enriched_df[enriched_df['_merge'] == 'left_only']
        print(f"Registros sem match no cadastro: {len(no_match)} ({len(no_match)/len(enriched_df)*100:.1f}%)")
        
        matched = enriched_df[enriched_df['_merge'] == 'both']
        print(f"Registros com match: {len(matched)} ({len(matched)/len(enriched_df)*100:.1f}%)")
        
        enriched_df = enriched_df.drop(columns=['_merge'])
        
        enriched_df['RegistroANS'] = enriched_df['RegistroANS'].fillna('')
        enriched_df['Modalidade'] = enriched_df['Modalidade'].fillna('NÃO IDENTIFICADO')
        enriched_df['UF'] = enriched_df['UF'].fillna('NÃO IDENTIFICADO')
        
        self.enrichment_log = {
            'total_records': len(enriched_df),
            'matched': len(matched),
            'no_match': len(no_match),
            'match_rate': len(matched) / len(enriched_df) * 100 if len(enriched_df) > 0 else 0
        }
        
        print(f"Campos adicionais adicionados: {len(enriched_df)} registros")
        
        return enriched_df
    
    def save_enrichment_log(self, output_path: Path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("LOG DE ENRIQUECIMENTO\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total de registros: {self.enrichment_log['total_records']}\n")
            f.write(f"Registros com match: {self.enrichment_log['matched']}\n")
            f.write(f"Registros sem match: {self.enrichment_log['no_match']}\n")
            f.write(f"Taxa de match: {self.enrichment_log['match_rate']:.2f}%\n")
        
        print(f"Log de enriquecimento salvo: {output_path}")
