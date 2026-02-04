import zipfile
import pandas as pd
from pathlib import Path
from typing import List, Optional
import chardet

class FileProcessor:
    """
    Processa arquivos de demonstrações contábeis da ANS.
    
    DECISÃO DE DESIGN - Processamento em Memória:
    Este processador utiliza estratégia de processamento em memória (load-all).
    
    Justificativa:
    - Trimestres da ANS contêm tipicamente 100-500MB de dados
    - Pandas é otimizado para operações em memória
    - Permite agregações e validações mais rápidas
    - Sistemas modernos possuem RAM suficiente (8GB+)
    
    Trade-offs:
    - Vantagens: Performance superior, código mais simples, suporte a operações complexas
    - Desvantagens: Limitado pela RAM disponível
    - Alternativa considerada: Processamento incremental com chunks (descartada por complexidade)
    
    Para volumes maiores (>2GB), considerar migração para Dask ou processamento incremental.
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.expense_keywords = ['evento', 'sinistro', 'despesa']
    
    def extract_zip(self, zip_path: Path) -> List[Path]:
        print(f"Extraindo: {zip_path.name}")
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_dir = self.data_dir / zip_path.stem
                extract_dir.mkdir(exist_ok=True)
                zip_ref.extractall(extract_dir)
                
                for file_path in extract_dir.rglob('*'):
                    if file_path.is_file():
                        extracted_files.append(file_path)
            
            print(f"Extraídos {len(extracted_files)} arquivos")
            return extracted_files
        except Exception as e:
            print(f"Erro ao extrair {zip_path}: {e}")
            return []
    
    def is_expense_file(self, file_path: Path) -> bool:
        """Verifica se o arquivo contém dados de despesas com eventos/sinistros"""
        filename_lower = file_path.name.lower()
        # Aceita arquivos CSV/TXT ou que contenham palavras-chave de despesas
        if file_path.suffix.lower() in ['.csv', '.txt', '.xlsx', '.xls']:
            return True
        return any(keyword in filename_lower for keyword in self.expense_keywords)
    
    def detect_encoding(self, file_path: Path) -> str:
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                return encoding if encoding else 'utf-8'
        except:
            return 'utf-8'
    
    def read_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        try:
            suffix = file_path.suffix.lower()
            encoding = self.detect_encoding(file_path)
            
            if suffix == '.csv':
                for sep in [',', ';', '|', '\t']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep, 
                                        low_memory=False, on_bad_lines='skip')
                        if len(df.columns) > 1:
                            return df
                    except:
                        continue
            
            elif suffix == '.txt':
                for sep in [';', '|', '\t', ',']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep,
                                        low_memory=False, on_bad_lines='skip')
                        if len(df.columns) > 1:
                            return df
                    except:
                        continue
            
            elif suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return df
            
            return None
        except Exception as e:
            print(f"Erro ao ler {file_path}: {e}")
            return None
    
    def normalize_columns(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        df.columns = df.columns.str.strip().str.upper()
        
        # Filtrar apenas linhas com EVENTO/SINISTRO
        if 'DESCRICAO' in df.columns:
            df = df[df['DESCRICAO'].str.contains('EVENTO|SINISTRO', case=False, na=False)]
        
        if len(df) == 0:
            return None
        
        reg_ans_cols = [col for col in df.columns if 'REG' in col and 'ANS' in col]
        data_cols = [col for col in df.columns if 'DATA' in col]
        valor_cols = [col for col in df.columns if 'VL_SALDO_FINAL' in col or 'SALDO_FINAL' in col]
        
        if not reg_ans_cols or not valor_cols:
            return None
        
        normalized_df = pd.DataFrame()
        
        normalized_df['REG_ANS'] = df[reg_ans_cols[0]]
        normalized_df['RazaoSocial'] = ''  # Será preenchido depois com dados cadastrais
        
        if data_cols:
            date_col = pd.to_datetime(df[data_cols[0]], errors='coerce')
            normalized_df['Ano'] = date_col.dt.year
            normalized_df['Trimestre'] = date_col.dt.quarter
        else:
            normalized_df['Ano'] = None
            normalized_df['Trimestre'] = None
        
        # Converter valores (formato brasileiro: 1.234,56)
        valor_col = df[valor_cols[0]].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        normalized_df['ValorDespesas'] = pd.to_numeric(valor_col, errors='coerce')
        
        return normalized_df
    
    def _extract_year(self, date_series: pd.Series) -> pd.Series:
        try:
            if pd.api.types.is_numeric_dtype(date_series):
                return date_series
            
            date_series = pd.to_datetime(date_series, errors='coerce')
            return date_series.dt.year
        except:
            return pd.Series([None] * len(date_series))
    
    def _extract_quarter(self, date_series: pd.Series) -> pd.Series:
        try:
            date_series = pd.to_datetime(date_series, errors='coerce')
            return date_series.dt.quarter
        except:
            return pd.Series([None] * len(date_series))
    
    def process_files(self, files: List[Path], year: int, quarter: int) -> pd.DataFrame:
        all_data = []
        
        for file_path in files:
            if not self.is_expense_file(file_path):
                continue
            
            df = self.read_file(file_path)
            if df is None or df.empty:
                continue
            
            normalized = self.normalize_columns(df)
            if normalized is None:
                continue
            
            if normalized['Ano'].isna().all():
                normalized['Ano'] = year
            if normalized['Trimestre'].isna().all():
                normalized['Trimestre'] = quarter
            
            all_data.append(normalized)
            print(f"Processado: {file_path.name} - {len(normalized)} registros")
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
