import pandas as pd
import numpy as np
from pathlib import Path
import sys

class DataAggregator:
    def aggregate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        print("Agregando dados...")
        
        aggregated = df.groupby(['RazaoSocial', 'UF']).agg({
            'ValorDespesas': ['sum', 'mean', 'std', 'count']
        }).reset_index()
        
        aggregated.columns = ['RazaoSocial', 'UF', 'TotalDespesas', 'MediaPorTrimestre', 
                              'DesvioPadrao', 'NumeroTrimestres']
        
        aggregated['DesvioPadrao'] = aggregated['DesvioPadrao'].fillna(0)
        
        aggregated = aggregated.sort_values('TotalDespesas', ascending=False)
        
        print(f"Agregação concluída: {len(aggregated)} grupos")
        print(f"\nTop 5 operadoras por valor total:")
        # Usar representação segura para evitar erro de encoding no console Windows
        try:
            print(aggregated[['RazaoSocial', 'UF', 'TotalDespesas']].head())
        except UnicodeEncodeError:
            print(aggregated[['RazaoSocial', 'UF', 'TotalDespesas']].head().to_string(index=False).encode('utf-8', errors='replace').decode('utf-8'))
        
        return aggregated
    
    def save_aggregated(self, df: pd.DataFrame, output_path: Path):
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\nArquivo agregado salvo: {output_path}")
        
        stats_path = output_path.parent / 'estatisticas_agregacao.txt'
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write("ESTATÍSTICAS DA AGREGAÇÃO\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total de grupos (Operadora/UF): {len(df)}\n")
            f.write(f"Operadoras únicas: {df['RazaoSocial'].nunique()}\n")
            f.write(f"UFs representadas: {df['UF'].nunique()}\n")
            f.write(f"Valor total de despesas: R$ {df['TotalDespesas'].sum():,.2f}\n")
            f.write(f"Média de despesas por grupo: R$ {df['TotalDespesas'].mean():,.2f}\n")
            f.write(f"Mediana de despesas: R$ {df['TotalDespesas'].median():,.2f}\n\n")
            
            f.write("TOP 10 OPERADORAS/UF POR DESPESAS TOTAIS\n")
            f.write("-" * 80 + "\n")
            top10 = df.head(10)
            for idx, row in top10.iterrows():
                f.write(f"{row['RazaoSocial']} ({row['UF']})\n")
                f.write(f"  Total: R$ {row['TotalDespesas']:,.2f}\n")
                f.write(f"  Média por trimestre: R$ {row['MediaPorTrimestre']:,.2f}\n")
                f.write(f"  Desvio padrão: R$ {row['DesvioPadrao']:,.2f}\n")
                f.write(f"  Número de trimestres: {int(row['NumeroTrimestres'])}\n\n")
            
            f.write("\nDISTRIBUIÇÃO POR UF\n")
            f.write("-" * 80 + "\n")
            uf_stats = df.groupby('UF').agg({
                'TotalDespesas': 'sum',
                'RazaoSocial': 'count'
            }).sort_values('TotalDespesas', ascending=False)
            
            for uf, row in uf_stats.iterrows():
                f.write(f"{uf}: R$ {row['TotalDespesas']:,.2f} ({int(row['RazaoSocial'])} operadoras)\n")
        
        print(f"Estatísticas salvas: {stats_path}")
        
        import zipfile
        zip_path = output_path.parent / 'Teste_Caetano_Matarazo_Granado.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(output_path, output_path.name)
            zipf.write(stats_path, stats_path.name)
        
        print(f"ZIP criado: {zip_path}")
