# TESTE 1 - Integração com API ANS

Integração com API de Dados Abertos da ANS para baixar e processar dados contábeis dos últimos 3 trimestres.

## Arquivos

- main.py: Orquestrador principal
- api_client.py: Cliente HTTP para API da ANS
- file_processor.py: Processamento de arquivos ZIP
- data_consolidator.py: Consolidação de dados
- cadastral_data.py: Enriquecimento com dados cadastrais

## Fluxo

1. Identificação de trimestres disponíveis
2. Download e extração de ZIPs
3. Processamento de arquivos (CSV, TXT, XLSX)
4. Consolidação de dados
5. Enriquecimento com dados cadastrais
6. Geração de saída (CSV, ZIP, log)

## Execução

```bash
python main.py
```

## Saída

- consolidado_despesas.csv (CNPJ, RazaoSocial, Trimestre, Ano, ValorDespesas)
- consolidado_despesas.zip
- inconsistencias_log.txt

## Tratamento de Inconsistências

### 1. CNPJs Duplicados com Razões Sociais Diferentes

**Problema**: Mesmo CNPJ aparece com diferentes razões sociais

**Abordagem**: 
- Detectar durante mapeamento cadastral
- Manter a razão social mais recente (último registro)
- Registrar em log

**Justificativa**: Razões sociais podem mudar (aquisições, renomeações)

### 2. Valores Negativos

**Problema**: Despesas com valores negativos

**Abordagem**: Converter para valor absoluto

**Justificativa**: 
- Valores negativos provavelmente são estornos/ajustes
- Para análise de volume de despesas, importa o valor absoluto
- Registrado em log para auditoria

### 3. Valores Zerados

**Problema**: Registros com ValorDespesas = 0

**Abordagem**: Remover da consolidação

**Justificativa**: 
- Não agregam informação relevante
- Podem ser registros placeholder ou incompletos
- Reduz volume sem perda de informação

### 4. Anos Inválidos

**Problema**: Datas fora do intervalo razoável (< 2000 ou > 2030)

**Abordagem**: Remover registro

**Justificativa**:
- Provavelmente erros de digitação ou parsing
- Impossível corrigir sem informação adicional
- Registrado em log

### 5. Trimestres Inválidos

**Problema**: Valores de trimestre fora de 1-4 ou NaN

**Abordagem**: Remover registro

**Justificativa**:
- Dados essenciais para análise temporal
- Sem trimestre válido, registro perde utilidade
- Registrado em log

### 6. Formatos de Data Inconsistentes

**Problema**: Datas em formatos variados (DD/MM/YYYY, YYYY-MM-DD, timestamps)

**Abordagem**: 
- Usar `pd.to_datetime(..., errors='coerce')` para parsing flexível
- Extrair ano e trimestre automaticamente
- Fallback para ano/trimestre do nome do arquivo

**Justificativa**: Maximiza recuperação de dados válidos

## Logs e Auditoria

O arquivo `inconsistencias_log.txt` documenta cada inconsistência:

```
LOG DE INCONSISTÊNCIAS
================================================================================

Tipo: VALOR_NEGATIVO
  reg_ans: 123456
  valor: -15000.50
  acao: Valor convertido para valor absoluto

Tipo: TRIMESTRE_INVALIDO
  reg_ans: 789012
  trimestre: 5
  acao: Registro removido
```

## Requisitos

```
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
openpyxl>=3.1.0
chardet>=5.0.0
```


