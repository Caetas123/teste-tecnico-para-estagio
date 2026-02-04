import pandas as pd
from pathlib import Path
from typing import Dict
import re

class DataConsolidator:
    def __init__(self):
        self.inconsistencies_log = []
    
    def clean_cnpj(self, cnpj: str) -> str:
        """Normaliza CNPJ: remove formatação e valida 14 dígitos"""
        if pd.isna(cnpj):
            return None
        cnpj_str = str(cnpj).strip()
        # Remove formatação (./-) 
        cnpj_clean = re.sub(r'\D', '', cnpj_str)
        # Valida 14 dígitos exatos
        if len(cnpj_clean) != 14:
            return None  # CNPJ inválido
        return cnpj_clean
    
    def consolidate_data(self, dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        print("Consolidando dados...")
        
        all_data = []
        for quarter_key, df in dataframes.items():
            if not df.empty:
                all_data.append(df)
        
        if not all_data:
            raise ValueError("Nenhum dado para consolidar")
        
        consolidated = pd.concat(all_data, ignore_index=True)
        
        # Primeiro trata datas inconsistentes
        consolidated = self._handle_date_inconsistencies(consolidated)
        
        # Agrupar por REG_ANS, Ano e Trimestre somando despesas
        consolidated = consolidated.groupby(['REG_ANS', 'Ano', 'Trimestre'], as_index=False).agg({
            'ValorDespesas': 'sum',
            'RazaoSocial': 'first'
        })
        
        # Trata valores inválidos
        consolidated = self._handle_invalid_values(consolidated)
        
        print(f"Total de registros consolidados: {len(consolidated)}")
        print(f"REG_ANS únicos: {consolidated['REG_ANS'].nunique()}")
        
        return consolidated
    
    def _handle_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        duplicate_cnpjs = df.groupby(['CNPJ', 'Ano', 'Trimestre']).filter(lambda x: len(x) > 1)
        
        if not duplicate_cnpjs.empty:
            print(f"Encontrados {len(duplicate_cnpjs)} registros duplicados")
            
            for cnpj in duplicate_cnpjs['CNPJ'].unique():
                cnpj_data = duplicate_cnpjs[duplicate_cnpjs['CNPJ'] == cnpj]
                razoes = cnpj_data['RazaoSocial'].unique()
                if len(razoes) > 1:
                    self.inconsistencies_log.append({
                        'tipo': 'CNPJ_MULTIPLAS_RAZOES',
                        'cnpj': cnpj,
                        'razoes': razoes.tolist(),
                        'acao': 'Mantida razão social mais recente'
                    })
            
            df = df.sort_values(['CNPJ', 'Ano', 'Trimestre', 'RazaoSocial'])
            df = df.drop_duplicates(subset=['CNPJ', 'Ano', 'Trimestre'], keep='last')
        
        return df
    
    def _handle_invalid_values(self, df: pd.DataFrame) -> pd.DataFrame:
        original_count = len(df)
        
        negative_values = df[df['ValorDespesas'] < 0]
        if not negative_values.empty:
            print(f"Encontrados {len(negative_values)} valores negativos")
            for _, row in negative_values.iterrows():
                self.inconsistencies_log.append({
                    'tipo': 'VALOR_NEGATIVO',
                    'reg_ans': row.get('REG_ANS', row.get('CNPJ', '')),
                    'valor': row['ValorDespesas'],
                    'acao': 'Valor convertido para valor absoluto'
                })
            df.loc[df['ValorDespesas'] < 0, 'ValorDespesas'] = df['ValorDespesas'].abs()
        
        zero_values = df[df['ValorDespesas'] == 0]
        if not zero_values.empty:
            print(f"Encontrados {len(zero_values)} valores zerados - removidos")
            df = df[df['ValorDespesas'] > 0]
        
        df['ValorDespesas'] = df['ValorDespesas'].fillna(0)
        
        return df
    
    def _handle_date_inconsistencies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trata inconsistências em datas (anos e trimestres inválidos)"""
        df['Ano'] = pd.to_numeric(df['Ano'], errors='coerce')
        df['Trimestre'] = pd.to_numeric(df['Trimestre'], errors='coerce')
        
        invalid_years = df[(df['Ano'] < 2000) | (df['Ano'] > 2030) | df['Ano'].isna()]
        if not invalid_years.empty:
            print(f"Encontrados {len(invalid_years)} anos inválidos")
            for _, row in invalid_years.head(10).iterrows():
                self.inconsistencies_log.append({
                    'tipo': 'ANO_INVALIDO',
                    'reg_ans': row.get('REG_ANS', ''),
                    'ano': row['Ano'],
                    'acao': 'Registro removido'
                })
            df = df[(df['Ano'] >= 2000) & (df['Ano'] <= 2030) & df['Ano'].notna()]
        
        invalid_quarters = df[(df['Trimestre'] < 1) | (df['Trimestre'] > 4) | df['Trimestre'].isna()]
        if not invalid_quarters.empty:
            print(f"Encontrados {len(invalid_quarters)} trimestres inválidos")
            for _, row in invalid_quarters.head(10).iterrows():
                self.inconsistencies_log.append({
                    'tipo': 'TRIMESTRE_INVALIDO',
                    'reg_ans': row.get('REG_ANS', ''),
                    'trimestre': row['Trimestre'],
                    'acao': 'Registro removido'
                })
            df = df[(df['Trimestre'] >= 1) & (df['Trimestre'] <= 4) & df['Trimestre'].notna()]
        
        return df
    
    def save_consolidated(self, df: pd.DataFrame, output_path: Path):
        csv_path = output_path.parent / 'consolidado_despesas.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"CSV salvo: {csv_path}")
        
        import zipfile
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(csv_path, csv_path.name)
        
        print(f"ZIP criado: {output_path}")
        
        log_path = output_path.parent / 'inconsistencias_log.txt'
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("LOG DE INCONSISTÊNCIAS\n")
            f.write("=" * 80 + "\n\n")
            for log_entry in self.inconsistencies_log:
                f.write(f"Tipo: {log_entry['tipo']}\n")
                for key, value in log_entry.items():
                    if key != 'tipo':
                        f.write(f"  {key}: {value}\n")
                f.write("\n")
        
        print(f"Log de inconsistências salvo: {log_path}")
