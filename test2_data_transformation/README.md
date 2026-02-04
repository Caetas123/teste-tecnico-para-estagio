# TESTE 2 - TRANSFORMAÇÃO E VALIDAÇÃO DE DADOS

## Visão Geral
Este módulo realiza validação, enriquecimento e agregação dos dados consolidados do Teste 1, aplicando regras de negócio e tratamento de inconsistências.

## Estrutura de Arquivos

- **main.py**: Orquestrador principal do processo
- **validators.py**: Validação de dados (CNPJ, valores, campos obrigatórios)
- **data_enrichment.py**: Enriquecimento com dados cadastrais
- **aggregator.py**: Agregação e cálculos estatísticos

## Fluxo de Execução

1. **Carregamento de Dados**
   - Lê o arquivo `consolidado_despesas.csv` gerado no Teste 1
   - Validação inicial de presença de arquivo

2. **Validação de Dados** (`validators.py`)
   - Valida formato e dígitos verificadores de CNPJ
   - Verifica valores numéricos positivos
   - Garante campos obrigatórios não vazios
   - Gera log detalhado de validação

3. **Enriquecimento** (`data_enrichment.py`)
   - Download dos dados cadastrais das operadoras ativas
   - Join com arquivo consolidado usando CNPJ
   - Adiciona colunas: RegistroANS, Modalidade, UF
   - Trata CNPJs sem match no cadastro

4. **Agregação** (`aggregator.py`)
   - Agrupa por RazaoSocial e UF
   - Calcula:
     - Total de despesas
     - Média por trimestre
     - Desvio padrão
   - Ordena por valor total (maior → menor)

5. **Saída**
   - `consolidado_enriquecido.csv` - Dados validados e enriquecidos
   - `despesas_agregadas.csv` - Dados agregados
   - `validacao_log.txt` - Log de validação
   - `enriquecimento_log.txt` - Log de enriquecimento

## Como Executar

```bash
# Certifique-se de que o ambiente virtual está ativado
cd test2_data_transformation
python main.py
```

**Pré-requisito:** Execute primeiro o Teste 1 para gerar `consolidado_despesas.csv`

## Decisões Técnicas

### 1. Estratégia de Validação de CNPJ

**Decisão**: Validação completa com dígitos verificadores + opção de correção/remoção

**Abordagem Implementada**:
- Validar formato (14 dígitos numéricos)
- Calcular e verificar dígitos verificadores
- Para CNPJs inválidos: **marcar como inválido mas manter no dataset**
- Registrar em log para análise posterior

**Justificativa**:
- CNPJs podem estar incorretos mas os dados de despesas são valiosos
- Permite análise posterior de qualidade de dados
- Mantém rastreabilidade (não remove silenciosamente)

**Trade-offs considerados**:

| Estratégia | Prós | Contras | Escolhida |
|------------|------|---------|-----------|  
| **Remover registros inválidos** | Dados 100% válidos | Perda de informação valiosa | Não |
| **Manter e marcar** | Mantém dados, permite análise | Requer tratamento downstream | Sim |
| **Tentar corrigir** | Recupera dados | Risco de correção incorreta | Não |
| **Ignorar validação** | Simples, sem perda | Dados inconsistentes | Não |

**Código de validação**:
```python
def validate_cnpj(cnpj: str) -> bool:
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', str(cnpj))
    
    # Verifica tamanho e dígitos verificadores
    if len(cnpj) != 14:
        return False
    
    # Cálculo dos dígitos verificadores (algoritmo padrão)
    # ... (implementação completa em validators.py)
    
    return digitos_calculados == cnpj[-2:]
```

### 2. Estratégia de Join com Dados Cadastrais

**Decisão**: Left join mantendo todos os registros consolidados

**Abordagem**:
- Join usando CNPJ como chave
- Manter todos os registros do consolidado (left join)
- Para registros sem match: preencher com valores padrão

**Tratamento de CNPJs sem match**:
```python
# Preencher campos vazios
df['RegistroANS'] = df['RegistroANS'].fillna('')
df['Modalidade'] = df['Modalidade'].fillna('NÃO IDENTIFICADO')
df['UF'] = df['UF'].fillna('NÃO IDENTIFICADO')
```

**Tratamento de CNPJs duplicados no cadastro**:
- Manter primeiro registro encontrado
- Registrar duplicatas em log
- Justificativa: Evitar multiplicação artificial de registros

**Trade-offs considerados**:

| Tipo de Join | Quando usar | Prós | Contras | Escolhida |
|--------------|-------------|------|---------|-----------|
| **Left Join** | Manter todos os registros de despesas | Não perde dados financeiros | Pode ter campos nulos | Sim |
| **Inner Join** | Apenas registros com match completo | Dados 100% consistentes | Perda de informação | Não |
| **Outer Join** | Manter tudo de ambos os lados | Visão completa | Dificulta análise | Não |

**Decisão**: Processamento completo em memória com Pandas

**Justificativa**:
- Volume estimado: ~50.000 registros após consolidação
- Tamanho em memória: ~10-20MB
- Pandas otimizado para operações in-memory
- Permite operações complexas (groupby, merge, agg)

**Trade-offs**:

| Estratégia | Volume suportado | Performance | Complexidade | Escolhida |
|------------|------------------|-------------|--------------|-----------|
| **In-memory (Pandas)** | Até 1-2GB | Rápida |  Simples | Sim |
| **Chunks (iterativo)** | Ilimitado | Moderada | Complexa | Não |
| **Dask/Spark** | Muito grande | Rápida (cluster) | Muito complexa | Não |

### 4. Estratégia de Ordenação

**Decisão**: Ordenação in-memory com Pandas `sort_values()`

**Abordagem**:
```python
df_agregado = df_agregado.sort_values(
    by='total_despesas', 
    ascending=False
)
```

**Justificativa**:
- Volume pós-agregação: ~1.000-5.000 registros (uma linha por operadora/UF)
- Ordenação in-memory é O(n log n), eficiente para esse volume
- Pandas usa Timsort (otimizado)

**Trade-offs**:

| Estratégia | Melhor para | Performance | Memória | Escolhida |
|------------|-------------|-------------|---------|-----------|
| **In-memory (Pandas)** | <100k registros | Alta | RAM moderada | Sim |
| **External sort** | Milhões de registros | Moderada | Pouca RAM | Não |
| **Database ORDER BY** | Dados já em BD | Alta | Zero | Aviso: não aplicável aqui |

### 1. Valores Numéricos Não Positivos

**Problema**: Valores de despesas ≤ 0

**Abordagem**: 
- Validar e marcar como inválido
- Registrar em log
- Não remover (permite análise)

### 2. Razão Social Vazia

**Problema**: Campo RazaoSocial nulo ou vazio

**Abordagem**:
- Marcar como inválido
- Tentar preencher com dados cadastrais se houver match por CNPJ
- Se não houver: usar "RAZÃO SOCIAL NÃO INFORMADA"

### 3. CNPJs em Múltiplos Formatos

**Detecção**:
- Normalização: remove pontos, barras e hífens
- Converte para string de 14 dígitos
- Valida após normalização

```python
# Antes: 00.000.000/0001-00, 00000000000100, 123456789012
# Depois: 00000000000100 (padronizado)
```

### 4. Registros Duplicados

**Problema**: Mesmo CNPJ + Ano + Trimestre aparece múltiplas vezes

**Abordagem**:
- Detectar duplicatas
- Somar valores de despesas (pode ser divisão por filiais)
- Registrar em log

## Estatísticas Geradas

O arquivo `despesas_agregadas.csv` contém:

| Coluna | Descrição | Fórmula |
|--------|-----------|---------|
| **RazaoSocial** | Nome da operadora | - |
| **UF** | Estado | - |
| **total_despesas** | Soma total | `SUM(ValorDespesas)` |
| **media_por_trimestre** | Média por trimestre | `MEAN(ValorDespesas)` |
| **desvio_padrao** | Variabilidade | `STDDEV(ValorDespesas)` |
| **numero_trimestres** | Quantidade de trimestres | `COUNT(DISTINCT Trimestre)` |

**Interpretação do desvio padrão**:
- Alto desvio: Despesas muito variáveis (sazonal ou crescimento rápido)
- Baixo desvio: Despesas estáveis

## Logs Gerados

### validacao_log.txt
```
Total de registros: 45,320
CNPJs válidos: 44,890 (99.05%)
CNPJs inválidos: 430 (0.95%)
Valores positivos: 45,100 (99.51%)
Valores inválidos: 220 (0.49%)
Razões sociais válidas: 45,320 (100%)
```

### enriquecimento_log.txt
```
Registros totais: 45,320
Matches encontrados: 43,200 (95.32%)
Sem match (CNPJ não cadastrado): 2,120 (4.68%)
CNPJs duplicados no cadastro: 15
Campos adicionados: RegistroANS, Modalidade, UF
```

## Dependências

```txt
pandas>=2.0.0
requests>=2.31.0
```

## Melhorias Futuras

1. **Validação avançada**: Verificar consistência temporal (despesas crescentes/decrescentes)
2. **Machine Learning**: Detectar outliers automaticamente
3. **Paralelização**: Processar validações em paralelo para grandes volumes
4. **API de validação**: Consultar API da Receita Federal para validar CNPJs em tempo real
