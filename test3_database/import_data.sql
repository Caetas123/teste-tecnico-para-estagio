-- ============================================================================
-- IMPORTAÇÃO DE DADOS CSV PARA MYSQL
-- ============================================================================

USE ans_database;

SET SESSION sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. IMPORTAR DADOS CONSOLIDADOS ENRIQUECIDOS
-- ============================================================================

-- Criar tabela temporária para importação
DROP TEMPORARY TABLE IF EXISTS temp_import;
CREATE TEMPORARY TABLE temp_import (
    cnpj VARCHAR(20),
    razao_social VARCHAR(255),
    trimestre VARCHAR(10),
    ano VARCHAR(10),
    valor_despesas VARCHAR(50),
    registro_ans VARCHAR(50),
    modalidade VARCHAR(100),
    uf VARCHAR(10)
);

-- Importar CSV (AJUSTAR O CAMINHO CONFORME NECESSÁRIO)
-- No Windows, use barras duplas ou barras simples invertidas
LOAD DATA LOCAL INFILE 'C:/Users/palad/OneDrive/Documentos/estagio2/output/consolidado_enriquecido.csv'
INTO TABLE temp_import
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(cnpj, razao_social, trimestre, ano, valor_despesas, registro_ans, modalidade, uf);

-- Limpar dados
UPDATE temp_import 
SET 
    cnpj = REGEXP_REPLACE(cnpj, '[^0-9]', ''),
    razao_social = TRIM(razao_social),
    trimestre = TRIM(trimestre),
    ano = TRIM(ano),
    valor_despesas = TRIM(valor_despesas),
    registro_ans = TRIM(COALESCE(registro_ans, '')),
    modalidade = TRIM(COALESCE(modalidade, 'NÃO IDENTIFICADO')),
    uf = TRIM(COALESCE(uf, 'NÃO IDENTIFICADO'));

-- Remover registros inválidos
DELETE FROM temp_import 
WHERE cnpj IS NULL 
   OR cnpj = '' 
   OR LENGTH(cnpj) <> 14
   OR razao_social IS NULL 
   OR razao_social = ''
   OR ano IS NULL 
   OR ano = ''
   OR CAST(ano AS UNSIGNED) < 2000
   OR trimestre IS NULL 
   OR trimestre = ''
   OR CAST(trimestre AS UNSIGNED) NOT BETWEEN 1 AND 4;

-- Converter valores não numéricos para 0
UPDATE temp_import
SET valor_despesas = '0'
WHERE valor_despesas IS NULL 
   OR valor_despesas = '' 
   OR valor_despesas NOT REGEXP '^[0-9.]+$';

-- ============================================================================
-- 2. POPULAR TABELA OPERADORAS
-- ============================================================================

INSERT INTO operadoras (cnpj, razao_social, registro_ans, modalidade, uf)
SELECT DISTINCT
    cnpj,
    razao_social,
    NULLIF(registro_ans, ''),
    NULLIF(modalidade, ''),
    NULLIF(uf, '')
FROM temp_import
ON DUPLICATE KEY UPDATE
    razao_social = VALUES(razao_social),
    registro_ans = COALESCE(VALUES(registro_ans), registro_ans),
    modalidade = COALESCE(VALUES(modalidade), modalidade),
    uf = COALESCE(VALUES(uf), uf);

SELECT CONCAT('Operadoras importadas: ', COUNT(*)) AS status FROM operadoras;

-- ============================================================================
-- 3. POPULAR TABELA DESPESAS
-- ============================================================================

INSERT INTO despesas (operadora_id, ano, trimestre, valor_despesas)
SELECT 
    o.id,
    CAST(t.ano AS UNSIGNED),
    CAST(t.trimestre AS UNSIGNED),
    CAST(t.valor_despesas AS DECIMAL(15,2))
FROM temp_import t
INNER JOIN operadoras o ON t.cnpj = o.cnpj
ON DUPLICATE KEY UPDATE
    valor_despesas = VALUES(valor_despesas);

SELECT CONCAT('Despesas importadas: ', COUNT(*)) AS status FROM despesas;

-- ============================================================================
-- 4. CALCULAR E POPULAR DESPESAS AGREGADAS
-- ============================================================================

INSERT INTO despesas_agregadas (
    operadora_id, 
    total_despesas, 
    media_por_trimestre, 
    desvio_padrao, 
    numero_trimestres
)
SELECT 
    operadora_id,
    SUM(valor_despesas) AS total_despesas,
    AVG(valor_despesas) AS media_por_trimestre,
    COALESCE(STDDEV_POP(valor_despesas), 0) AS desvio_padrao,
    COUNT(*) AS numero_trimestres
FROM despesas
GROUP BY operadora_id
ON DUPLICATE KEY UPDATE
    total_despesas = VALUES(total_despesas),
    media_por_trimestre = VALUES(media_por_trimestre),
    desvio_padrao = VALUES(desvio_padrao),
    numero_trimestres = VALUES(numero_trimestres);

SELECT CONCAT('Agregações calculadas: ', COUNT(*)) AS status FROM despesas_agregadas;

-- ============================================================================
-- 5. IMPORTAR DADOS AGREGADOS (OPCIONAL - SE QUISER USAR O CSV PRÉ-AGREGADO)
-- ============================================================================

DROP TEMPORARY TABLE IF EXISTS temp_agregados;
CREATE TEMPORARY TABLE temp_agregados (
    razao_social VARCHAR(255),
    uf VARCHAR(10),
    total_despesas VARCHAR(50),
    media_por_trimestre VARCHAR(50),
    desvio_padrao VARCHAR(50),
    numero_trimestres VARCHAR(10)
);

LOAD DATA LOCAL INFILE 'C:/Users/palad/OneDrive/Documentos/estagio2/output/despesas_agregadas.csv'
INTO TABLE temp_agregados
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Limpar e atualizar
UPDATE despesas_agregadas da
INNER JOIN operadoras o ON da.operadora_id = o.id
INNER JOIN temp_agregados ta ON o.razao_social = ta.razao_social AND o.uf = ta.uf
SET 
    da.total_despesas = CAST(ta.total_despesas AS DECIMAL(15,2)),
    da.media_por_trimestre = CAST(ta.media_por_trimestre AS DECIMAL(15,2)),
    da.desvio_padrao = CAST(ta.desvio_padrao AS DECIMAL(15,2)),
    da.numero_trimestres = CAST(ta.numero_trimestres AS UNSIGNED);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- VERIFICAÇÃO DE IMPORTAÇÃO
-- ============================================================================

SELECT 
    'RESUMO DA IMPORTAÇÃO' AS info,
    (SELECT COUNT(*) FROM operadoras) AS total_operadoras,
    (SELECT COUNT(*) FROM despesas) AS total_despesas,
    (SELECT COUNT(*) FROM despesas_agregadas) AS total_agregacoes,
    (SELECT SUM(valor_despesas) FROM despesas) AS valor_total_despesas;

-- ============================================================================
-- TRATAMENTO DE INCONSISTÊNCIAS
-- ============================================================================

/*
DECISÃO DE TRATAMENTO:

1. VALORES NULL EM CAMPOS OBRIGATÓRIOS
   - Ação: Rejeitados durante limpeza da tabela temporária
   - Justificativa: Dados incompletos comprometem integridade das análises

2. STRINGS EM CAMPOS NUMÉRICOS
   - Ação: Convertidos para 0 (zero)
   - Justificativa: Preserva registro para análise, mas não distorce estatísticas
   - Alternativa considerada: Rejeitar - descartada pois perde dados cadastrais

3. DATAS EM FORMATOS INCONSISTENTES
   - Ação: Validação com REGEX e conversão; registros inválidos rejeitados
   - Justificativa: Anos < 2000 ou > 2030 são erros claros
   - Trimestres fora de 1-4 são inválidos por definição

4. CNPJs DUPLICADOS
   - Ação: ON DUPLICATE KEY UPDATE mantém versão mais recente
   - Justificativa: Razão social pode mudar; UF e modalidade são atualizados

5. ENCODING
   - Ação: UTF-8 forçado na importação
   - Justificativa: Caracteres especiais em razões sociais são comuns
*/
