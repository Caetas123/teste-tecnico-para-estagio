# TESTE 3 - BANCO DE DADOS E ANÁLISE

## Visão Geral
Este módulo contém scripts SQL para criação de schema, importação de dados e queries analíticas sobre os dados de despesas das operadoras de planos de saúde.

## Estrutura de Arquivos

- **schema.sql**: Criação de tabelas, índices e views
- **import_data.sql**: Scripts para importação dos CSVs
- **queries.sql**: Queries analíticas para responder às questões do teste
- **main.py**: Script Python auxiliar para validação e testes

## Arquitetura do Banco de Dados

### Modelo de Dados

```
┌─────────────────┐
│   operadoras    │
├─────────────────┤
│ id (PK)         │
│ cnpj (UK)       │
│ razao_social    │
│ registro_ans    │
│ modalidade      │
│ uf              │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│    despesas     │
├─────────────────┤
│ id (PK)         │
│ operadora_id(FK)│
│ ano             │
│ trimestre       │
│ valor_despesas  │
└─────────────────┘
         │
         │ 1:1
         ▼
┌─────────────────────┐
│ despesas_agregadas  │
├─────────────────────┤
│ id (PK)             │
│ operadora_id (FK)   │
│ total_despesas      │
│ media_por_trimestre │
│ desvio_padrao       │
│ numero_trimestres   │
└─────────────────────┘
```

## Como Executar

### 1. Criar o Banco de Dados

```bash
mysql -u root -p < schema.sql
```

**Resultado**: Criação do database `ans_database` com 3 tabelas principais.

### 2. Importar Dados dos CSVs

```bash
mysql -u root -p ans_database < import_data.sql
```

**Pré-requisitos**:
- CSVs gerados pelos Testes 1 e 2 devem estar em `../output/`
- Arquivos necessários:
  - `consolidado_despesas.csv`
  - `despesas_agregadas.csv`
  - `operadoras_ativas.csv` (em `../data/`)

**Atenção**: Ajuste o caminho dos arquivos no script se necessário.

### 3. Executar Queries Analíticas

```bash
mysql -u root -p ans_database < queries.sql > resultados_queries.txt
```

**Saída**: Arquivo `resultados_queries.txt` com os resultados das 3 queries principais.

## Decisões Técnicas

### 1. Trade-off: Normalização vs Desnormalização

**Decisão**: **Modelo semi-normalizado (Opção B+)**

**Estrutura escolhida**:
-  Tabela `operadoras` separada (normalizada)
-  Tabela `despesas` normalizada com FK
-  Tabela `despesas_agregadas` desnormalizada (cache)

**Justificativa**:

| Critério | Normalizado | Desnormalizado | Escolhido (Híbrido) |
|----------|-------------|----------------|---------------------|
| **Volume de dados** | Eficiente | Redundante |  Balanceado |
| **Frequência de updates** | Poucos updates | Dificulta updates |  Updates raros (trimestral) |
| **Queries analíticas** | Requer JOINs | Rápido (sem JOIN) |  Views + tabela agregada |
| **Integridade** | Alta | Baixa |  FKs garantem integridade |
| **Manutenibilidade** |  Alta |  Baixa |  Views simplificam |

**Benefícios da abordagem híbrida**:
1. **Operadoras normalizadas**: Evita duplicação de dados cadastrais
2. **Despesas normalizadas**: Cada trimestre é um registro único
3. **Agregados desnormalizados**: Performance em queries de dashboard
4. **Views**: Simplificam queries complexas

**Estrutura de tabelas**:

```sql
-- Normalizada: dados mestres
CREATE TABLE operadoras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cnpj CHAR(14) UNIQUE,
    razao_social VARCHAR(255),
    registro_ans VARCHAR(50),
    modalidade VARCHAR(100),
    uf CHAR(2)
);

-- Normalizada: transações
CREATE TABLE despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operadora_id INT,
    ano SMALLINT,
    trimestre TINYINT,
    valor_despesas DECIMAL(15,2),
    FOREIGN KEY (operadora_id) REFERENCES operadoras(id)
);

-- Desnormalizada: cache de agregações
CREATE TABLE despesas_agregadas (
    operadora_id INT PRIMARY KEY,
    total_despesas DECIMAL(15,2),
    media_por_trimestre DECIMAL(15,2),
    ...
);
```

**Alternativas consideradas**:

**Opção A (Totalmente Desnormalizada)**:
```sql
-- UMA ÚNICA TABELA
CREATE TABLE dados_completos (
    cnpj, razao_social, uf, modalidade,
    ano, trimestre, valor_despesas
);
```
 Descartada por:
- Alta redundância (razão social repetida para cada trimestre)
- Risco de inconsistência (updates parciais)
- Maior uso de disco

**Opção B (Totalmente Normalizada)**:
```sql
-- Múltiplas tabelas com FKs
operadoras → despesas → trimestres → ...
```
 Descartada por:
- JOINs complexos em queries analíticas
- Performance inferior para dashboards
- Over-engineering para volume de dados moderado

### 2. Trade-off: Tipos de Dados para Valores Monetários

**Decisão**: `DECIMAL(15,2)`

**Comparação**:

| Tipo | Precisão | Performance | Storage | Escolhido |
|------|----------|-------------|---------|-----------|
| **DECIMAL(15,2)** | Exata | Moderada | 7 bytes | Sim |
| **FLOAT/DOUBLE** | Aproximada | Alta | 4-8 bytes | Não |
| **INTEGER (centavos)** | Exata | Alta | 4 bytes | Não |

```sql
-- DECIMAL: Precisão exata para valores monetários
valor_despesas DECIMAL(15,2)
-- Suporta até: 9,999,999,999,999.99 (~ 10 trilhões)
-- Precisão: 2 casas decimais (centavos)
```

**Por que não FLOAT?**
```sql
-- FLOAT: Perde precisão em operações aritméticas
SELECT 0.1 + 0.2;  -- Pode retornar 0.30000000000000004
--  INACEITÁVEL para valores financeiros
```

**Por que não INTEGER (centavos)?**
```sql
-- INTEGER: Armazena valores em centavos
valor_centavos INT  -- 1000 = R$ 10,00
--  Vantagens: Performance, precisão
--  Desvantagens:
--    - Requer conversão em todas as queries
--    - Legibilidade reduzida
--    - Não há ganho significativo para esse volume
```

**Casos de uso por tipo**:

| Tipo | Melhor para | Exemplo |
|------|-------------|---------|
| **DECIMAL** | Finanças, contabilidade | Despesas médicas, faturamento |
| **FLOAT** | Cálculos científicos aproximados | Coordenadas geográficas |
| **INTEGER (centavos)** | Sistemas de alta frequência | Trading de ações, criptomoedas |

### 3. Trade-off: Tipos de Dados para Datas

**Decisão**: Armazenar `ano SMALLINT` e `trimestre TINYINT` separadamente

**Justificativa**:

```sql
-- Escolha: Campos separados
ano SMALLINT         -- 2024, 2025, etc.
trimestre TINYINT    -- 1, 2, 3, 4
```

**Comparação**:

| Tipo | Storage | Queries | Validação | Escolhido |
|------|---------|---------|-----------|-----------|
| **ano + trimestre (INT)** | 3 bytes | Fácil filtrar | CHECK constraint | Sim |
| **DATE ('2024-03-31')** | 3 bytes | Requer QUARTER() | Complexa | Não |
| **VARCHAR ('2024Q1')** | 6+ bytes | Requer parsing | Difícil | Não |
| **TIMESTAMP** | 4 bytes | Requer QUARTER() | Overhead | Não |

```sql
--  Queries simples e rápidas
SELECT * FROM despesas 
WHERE ano = 2024 AND trimestre IN (1, 2);

--  Agregações diretas
GROUP BY ano, trimestre;

--  Validação nativa
CHECK (trimestre BETWEEN 1 AND 4);
```

**Alternativa com DATE**:
```sql
--  Requer funções adicionais
SELECT * FROM despesas 
WHERE YEAR(data) = 2024 AND QUARTER(data) IN (1, 2);

--  Ambiguidade: qual data usar no trimestre?
-- Início: 2024-01-01
-- Fim: 2024-03-31
-- Meio: 2024-02-15
```

## Índices e Performance

### Índices Criados

```sql
-- Tabela operadoras
UNIQUE KEY uk_cnpj (cnpj)              -- Busca por CNPJ
INDEX idx_razao_social (razao_social)  -- Busca por nome
INDEX idx_uf (uf)                      -- Filtro por estado
INDEX idx_modalidade (modalidade)      -- Filtro por tipo

-- Tabela despesas
UNIQUE KEY uk_operadora_periodo (operadora_id, ano, trimestre)
INDEX idx_ano_trimestre (ano, trimestre)
INDEX idx_valor (valor_despesas)
INDEX idx_periodo (ano, trimestre, operadora_id)  -- Covering index

-- Tabela despesas_agregadas
INDEX idx_total_despesas (total_despesas DESC)  -- Ordenação rápida
```

**Justificativa dos índices**:

| Índice | Objetivo | Query beneficiada |
|--------|----------|-------------------|
| `uk_operadora_periodo` | Evitar duplicatas | INSERT/UPDATE |
| `idx_ano_trimestre` | Filtro por período | WHERE ano = X AND trimestre = Y |
| `idx_periodo` | Covering index | Query 1 (crescimento) |
| `idx_total_despesas DESC` | Top N | Query 2 (maiores despesas) |

## Tratamento de Inconsistências na Importação

### 1. Valores NULL em Campos Obrigatórios

**Problema**: CNPJ ou Razão Social NULL

**Abordagem**:
```sql
-- Opção 1: Rejeitar registro (escolhida)
LOAD DATA INFILE ...
SET cnpj = NULLIF(@cnpj, ''),
    razao_social = NULLIF(@razao_social, '');

-- Validação posterior
DELETE FROM operadoras WHERE cnpj IS NULL OR razao_social IS NULL;
```

**Alternativa considerada**:
```sql
-- Opção 2: Usar valor padrão
SET cnpj = COALESCE(@cnpj, 'DESCONHECIDO');
```
 Descartada: Cria dados fictícios, dificulta análise

**Justificativa**: 
- Registros sem CNPJ não podem ser associados a despesas
- Melhor rejeitar que criar dados inválidos
- Log de rejeição permite investigação

### 2. Strings em Campos Numéricos

**Problema**: valor_despesas = 'N/A' ou 'indefinido'

**Abordagem**:
```sql
SET valor_despesas = 
    CASE 
        WHEN @valor REGEXP '^[0-9]+\.?[0-9]*$' 
        THEN CAST(@valor AS DECIMAL(15,2))
        ELSE NULL 
    END;

-- Remover registros inválidos
DELETE FROM despesas WHERE valor_despesas IS NULL;
```

**Logging**:
```sql
-- Contar rejeitados
SELECT COUNT(*) AS rejeitados 
FROM temp_import 
WHERE valor_despesas IS NULL;
```

### 3. Datas em Formatos Inconsistentes

**Problema**: Ano = '2024/01' ou 'Q1-2024'

**Abordagem**:
```sql
-- Parsing flexível
SET ano = 
    CASE
        WHEN @ano REGEXP '^[0-9]{4}$' THEN CAST(@ano AS SMALLINT)
        WHEN @ano REGEXP '^[0-9]{4}/' THEN CAST(LEFT(@ano, 4) AS SMALLINT)
        ELSE NULL
    END;

SET trimestre =
    CASE
        WHEN @trimestre BETWEEN 1 AND 4 THEN @trimestre
        WHEN @trimestre LIKE 'Q%' THEN CAST(SUBSTRING(@trimestre, 2, 1) AS TINYINT)
        WHEN @trimestre LIKE '%T' THEN CAST(LEFT(@trimestre, 1) AS TINYINT)
        ELSE NULL
    END;
```

**Validação**:
```sql
-- Garantir intervalos válidos
DELETE FROM despesas 
WHERE ano < 2000 OR ano > 2030 
   OR trimestre NOT BETWEEN 1 AND 4;
```

### 4. Encoding UTF-8

**Configuração**:
```sql
-- Garantir encoding correto
SET NAMES utf8mb4;
CHARACTER SET utf8mb4;

-- Na importação
LOAD DATA INFILE ... CHARACTER SET utf8mb4;
```

**Problemas comuns**:
- `'São Paulo'` importado como `'S├úo Paulo'` → Encoding errado
- Solução: Sempre usar UTF8MB4

## Queries Analíticas

### Query 1: Top 5 Operadoras com Maior Crescimento

```sql
WITH primeiro_ultimo_trimestre AS (
    SELECT 
        operadora_id,
        MIN(ano * 10 + trimestre) AS primeiro_periodo,
        MAX(ano * 10 + trimestre) AS ultimo_periodo
    FROM despesas
    GROUP BY operadora_id
    HAVING COUNT(DISTINCT CONCAT(ano, '-', trimestre)) >= 2
),
valores_periodos AS (
    SELECT 
        d.operadora_id,
        MAX(CASE WHEN d.ano * 10 + d.trimestre = p.primeiro_periodo 
            THEN d.valor_despesas END) AS valor_inicial,
        MAX(CASE WHEN d.ano * 10 + d.trimestre = p.ultimo_periodo 
            THEN d.valor_despesas END) AS valor_final
    FROM despesas d
    JOIN primeiro_ultimo_trimestre p ON d.operadora_id = p.operadora_id
    GROUP BY d.operadora_id
)
SELECT 
    o.razao_social,
    v.valor_inicial,
    v.valor_final,
    ((v.valor_final - v.valor_inicial) / v.valor_inicial * 100) AS crescimento_percentual
FROM valores_periodos v
JOIN operadoras o ON v.operadora_id = o.id
WHERE v.valor_inicial > 0
ORDER BY crescimento_percentual DESC
LIMIT 5;
```

**Desafios tratados**:
-  Operadoras sem dados em todos os trimestres → `HAVING COUNT >= 2`
-  Divisão por zero → `WHERE valor_inicial > 0`
-  Identificação de primeiro/último período → CTEs

### Query 2: Distribuição de Despesas por UF

```sql
SELECT 
    o.uf,
    SUM(d.valor_despesas) AS total_despesas,
    COUNT(DISTINCT o.id) AS numero_operadoras,
    AVG(d.valor_despesas) AS media_por_operadora
FROM despesas d
JOIN operadoras o ON d.operadora_id = o.id
GROUP BY o.uf
ORDER BY total_despesas DESC
LIMIT 5;
```

**Desafio adicional**: Calcular média por operadora (não apenas total)

### Query 3: Operadoras Acima da Média em ≥2 Trimestres

**Trade-off técnico**: Múltiplas abordagens possíveis

**Opção A: Subquery correlacionada** (escolhida)
```sql
SELECT COUNT(DISTINCT operadora_id) AS total_operadoras
FROM (
    SELECT 
        d.operadora_id,
        d.ano,
        d.trimestre,
        d.valor_despesas,
        (SELECT AVG(valor_despesas) 
         FROM despesas d2 
         WHERE d2.ano = d.ano AND d2.trimestre = d.trimestre) AS media_trimestre
    FROM despesas d
) AS despesas_com_media
WHERE valor_despesas > media_trimestre
GROUP BY operadora_id
HAVING COUNT(*) >= 2;
```

**Opção B: Window functions**
```sql
WITH medias AS (
    SELECT 
        operadora_id,
        ano,
        trimestre,
        valor_despesas,
        AVG(valor_despesas) OVER (PARTITION BY ano, trimestre) AS media
    FROM despesas
)
SELECT COUNT(DISTINCT operadora_id)
FROM medias
WHERE valor_despesas > media
GROUP BY operadora_id
HAVING COUNT(*) >= 2;
```

**Opção C: Temp tables**
```sql
CREATE TEMPORARY TABLE medias_trimestre AS
SELECT ano, trimestre, AVG(valor_despesas) AS media
FROM despesas GROUP BY ano, trimestre;

SELECT COUNT(DISTINCT d.operadora_id)
FROM despesas d
JOIN medias_trimestre m USING (ano, trimestre)
WHERE d.valor_despesas > m.media
GROUP BY d.operadora_id
HAVING COUNT(*) >= 2;
```

**Comparação**:

| Abordagem | Performance | Legibilidade | Manutenibilidade | Escolhida |
|-----------|-------------|--------------|------------------|-----------|
| **Subquery** | Moderada | Alta | Alta | Sim |
| **Window Functions** | Alta | Moderada | Moderada | Não |
| **Temp Tables** | Alta | Alta | Baixa (gerenciamento) | Não |
-  Compatível com MySQL 5.7+ (sem necessidade de 8.0+)
-  Código autocontido (uma query)
-  Fácil de entender e debugar
-  Performance: Adequada para volume esperado (<1M registros)

## Views Auxiliares

### vw_despesas_completas
```sql
-- Join pré-calculado para facilitar queries
CREATE VIEW vw_despesas_completas AS
SELECT 
    d.id, o.cnpj, o.razao_social, o.uf, o.modalidade,
    d.ano, d.trimestre, d.valor_despesas,
    CONCAT(d.ano, '-Q', d.trimestre) AS periodo
FROM despesas d
INNER JOIN operadoras o ON d.operadora_id = o.id;
```

**Uso**: Simplifica queries exploratórias
```sql
-- Em vez de:
SELECT * FROM despesas d JOIN operadoras o ON ...

-- Use:
SELECT * FROM vw_despesas_completas WHERE uf = 'SP';
```

## Dependências

```txt
MySQL 8.0+
mysql-connector-python>=8.0.0 (para o script Python auxiliar)
```

## Execução Completa (Ordem Recomendada)

```bash
# 1. Criar estrutura
mysql -u root -p < schema.sql

# 2. Importar dados
mysql -u root -p ans_database < import_data.sql

# 3. Executar queries analíticas
mysql -u root -p ans_database < queries.sql > ../output/resultados_queries.txt

# 4. (Opcional) Validar com Python
python main.py
```

## Melhorias Futuras

1. **Particionamento**: Particionar tabela `despesas` por ano para melhor performance
2. **Materialização**: Converter views em tabelas materializadas
3. **Triggers**: Atualizar `despesas_agregadas` automaticamente via triggers
4. **Stored Procedures**: Encapsular queries complexas
5. **Auditoria**: Tabelas de log para rastrear mudanças
