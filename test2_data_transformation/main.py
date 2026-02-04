import pandas as pd
from pathlib import Path
from validators import DataValidator
from data_enrichment import DataEnrichment
from aggregator import DataAggregator
from config.settings import DATA_DIR, OUTPUT_DIR

def main():
    print("=" * 80)
    print("TESTE 2: TRANSFORMAÇÃO E VALIDAÇÃO DE DADOS")
    print("=" * 80)
    
    consolidado_path = OUTPUT_DIR / 'consolidado_despesas.csv'
    if not consolidado_path.exists():
        print(f"Erro: Arquivo {consolidado_path} não encontrado!")
        print("Execute primeiro o teste 1 (test1_api_integration/main.py)")
        return
    
    print("\n1. CARREGANDO DADOS CONSOLIDADOS")
    print("-" * 80)
    df = pd.read_csv(consolidado_path)
    print(f"Registros carregados: {len(df)}")
    
    print("\n2. VALIDAÇÃO DE DADOS")
    print("-" * 80)
    validator = DataValidator()
    validated_df = validator.validate_dataframe(df)
    validator.save_validation_log(OUTPUT_DIR / 'validacao_log.txt')
    
    print("\n3. ENRIQUECIMENTO COM CAMPOS ADICIONAIS (RegistroANS, Modalidade, UF)")
    print("-" * 80)
    enrichment = DataEnrichment()
    
    try:
        operadoras_file = enrichment.download_operadoras_data(DATA_DIR)
        operadoras_df = enrichment.load_operadoras_data(operadoras_file)
    except Exception as e:
        print(f"Erro ao carregar dados cadastrais: {e}")
        print("Continuando sem campos adicionais...")
        operadoras_df = pd.DataFrame()
    
    if not operadoras_df.empty:
        enriched_df = enrichment.enrich_with_additional_fields(validated_df, operadoras_df)
        enrichment.save_enrichment_log(OUTPUT_DIR / 'enriquecimento_log.txt')
    else:
        enriched_df = validated_df.copy()
        enriched_df['RegistroANS'] = ''
        enriched_df['Modalidade'] = 'NÃO IDENTIFICADO'
        enriched_df['UF'] = 'NÃO IDENTIFICADO'
    
    enriched_csv = OUTPUT_DIR / 'consolidado_enriquecido.csv'
    enriched_df.to_csv(enriched_csv, index=False, encoding='utf-8')
    print(f"Dados com campos adicionais salvos: {enriched_csv}")
    
    print("\n4. AGREGAÇÃO DE DADOS")
    print("-" * 80)
    aggregator = DataAggregator()
    aggregated_df = aggregator.aggregate_data(enriched_df)
    
    aggregated_path = OUTPUT_DIR / 'despesas_agregadas.csv'
    aggregator.save_aggregated(aggregated_df, aggregated_path)
    
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS FINAIS")
    print("=" * 80)
    print(f"Registros originais: {len(df)}")
    print(f"Registros validados: {len(validated_df)}")
    print(f"Registros enriquecidos: {len(enriched_df)}")
    print(f"Grupos agregados: {len(aggregated_df)}")
    print(f"Taxa de validação: {len(validated_df)/len(df)*100:.1f}%")
    
    print("\n" + "=" * 80)
    print("TESTE 2 CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print(f"\nArquivos gerados:")
    print(f"  - {enriched_csv}")
    print(f"  - {aggregated_path}")
    print(f"  - {OUTPUT_DIR / 'validacao_log.txt'}")
    print(f"  - {OUTPUT_DIR / 'enriquecimento_log.txt'}")
    print(f"  - {OUTPUT_DIR / 'estatisticas_agregacao.txt'}")

if __name__ == "__main__":
    main()
