# Output

Arquivos gerados pelos testes.

## Estrutura

```
output/
├── consolidado_despesas.csv
├── consolidado_despesas.zip
├── inconsistencias_log.txt
├── consolidado_enriquecido.csv
├── despesas_agregadas.csv
├── validacao_log.txt
├── enriquecimento_log.txt
├── estatisticas_agregacao.txt
└── resultados_queries.txt
```

## Principais Arquivos

### consolidado_despesas.csv
Dados consolidados dos últimos 3 trimestres.

Colunas: CNPJ, RazaoSocial, Trimestre, Ano, ValorDespesas

### despesas_agregadas.csv
Dados agregados por operadora e UF.

Colunas: RazaoSocial, UF, total_despesas, media_por_trimestre, desvio_padrao, numero_trimestres

## Executar

```powershell
cd test1_api_integration
python main.py

cd ..\test2_data_transformation
python main.py

mysql -u root -p ans_database < ..\test3_database\queries.sql > ..\output\resultados_queries.txt
```

## Logs

- inconsistencias_log.txt: CNPJs duplicados, valores negativos, trimestres inválidos
- validacao_log.txt: Estatísticas de validação
- enriquecimento_log.txt: Informações sobre enriquecimento com dados cadastrais

## Limpar Arquivos

```powershell
Remove-Item -Path output\* -Force
```

Atenção: Este comando apaga todos os arquivos gerados.
