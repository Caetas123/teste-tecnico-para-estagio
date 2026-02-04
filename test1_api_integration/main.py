from pathlib import Path
from api_client import ANSApiClient
from file_processor import FileProcessor
from data_consolidator import DataConsolidator
from cadastral_data import CadastralDataFetcher
from config.settings import DATA_DIR, OUTPUT_DIR

def main():
    print("=" * 80)
    print("TESTE 1: INTEGRAÇÃO COM API ANS")
    print("=" * 80)
    
    api_client = ANSApiClient()
    file_processor = FileProcessor(DATA_DIR)
    consolidator = DataConsolidator()
    cadastral_fetcher = CadastralDataFetcher(DATA_DIR)
    
    quarters = api_client.get_available_quarters(num_quarters=3)
    
    if not quarters:
        print("Nenhum trimestre encontrado!")
        return
    
    print("\nTrimestres selecionados:")
    for q in quarters:
        print(f"  - {q['year']} Q{q['quarter']}")
    
    quarterly_data = {}
    
    for quarter_info in quarters:
        print(f"\n{'=' * 80}")
        print(f"Processando: {quarter_info['year']} Q{quarter_info['quarter']}")
        print(f"{'=' * 80}")
        
        expense_files = api_client.get_expense_files(quarter_info['url'])
        print(f"Encontrados {len(expense_files)} arquivos de despesas")
        
        extracted_files = []
        for file_url in expense_files:
            filename = file_url.split('/')[-1]
            destination = DATA_DIR / filename
            
            if api_client.download_file(file_url, destination):
                files = file_processor.extract_zip(destination)
                extracted_files.extend(files)
        
        df = file_processor.process_files(
            extracted_files,
            quarter_info['year'],
            quarter_info['quarter']
        )
        
        if not df.empty:
            key = f"{quarter_info['year']}_Q{quarter_info['quarter']}"
            quarterly_data[key] = df
            print(f"Dados carregados: {len(df)} registros")
    
    print(f"\n{'=' * 80}")
    print("CONSOLIDAÇÃO DE DADOS")
    print(f"{'=' * 80}")
    
    consolidated_df = consolidator.consolidate_data(quarterly_data)
    
    print(f"\n{'=' * 80}")
    print("ENRIQUECIMENTO COM DADOS CADASTRAIS")
    print(f"{'=' * 80}")
    
    cadastral_df = cadastral_fetcher.download_cadastral_data()
    if cadastral_df is not None:
        consolidated_df = cadastral_fetcher.map_reg_ans_to_cnpj(consolidated_df, cadastral_df)
    else:
        print("AVISO: Dados cadastrais não disponíveis, usando REG_ANS como CNPJ")
        consolidated_df['CNPJ'] = consolidated_df['REG_ANS'].astype(str)
        consolidated_df['RazaoSocial'] = consolidated_df['RazaoSocial'].fillna('')
    
    consolidated_df = consolidated_df[['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']]
    
    output_file = OUTPUT_DIR / 'consolidado_despesas.zip'
    consolidator.save_consolidated(consolidated_df, output_file)
    
    print(f"\n{'=' * 80}")
    print("ESTATÍSTICAS FINAIS")
    print(f"{'=' * 80}")
    print(f"Total de registros: {len(consolidated_df)}")
    print(f"Operadoras únicas: {consolidated_df['CNPJ'].nunique()}")
    print(f"Valor total: R$ {consolidated_df['ValorDespesas'].sum():,.2f}")
    print(f"\nDistribuição por trimestre:")
    print(consolidated_df.groupby(['Ano', 'Trimestre']).size())
    
    print(f"\n{'=' * 80}")
    print("TESTE 1 CONCLUÍDO COM SUCESSO!")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()
