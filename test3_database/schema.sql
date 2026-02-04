-- ============================================================================
-- TESTE 3: BANCO DE DADOS E ANÁLISE
-- Criação de schema para dados ANS
-- MySQL 8.0
-- ============================================================================

DROP DATABASE IF EXISTS ans_database;
CREATE DATABASE ans_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ans_database;

-- ============================================================================
-- TABELA: operadoras
-- Armazena dados cadastrais das operadoras
-- ============================================================================

CREATE TABLE operadoras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cnpj CHAR(14),
    razao_social VARCHAR(255) NOT NULL,
    registro_ans VARCHAR(50),
    modalidade VARCHAR(100),
    uf CHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cnpj (cnpj),
    INDEX idx_razao_social (razao_social),
    INDEX idx_uf (uf),
    INDEX idx_modalidade (modalidade)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Dados cadastrais das operadoras de planos de saúde';

-- ============================================================================
-- TABELA: despesas
-- Armazena dados de despesas por operadora e trimestre
-- ============================================================================

CREATE TABLE despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operadora_id INT NOT NULL,
    ano SMALLINT NOT NULL,
    trimestre TINYINT NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    valor_despesas DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operadora_id) REFERENCES operadoras(id) ON DELETE CASCADE,
    UNIQUE KEY uk_operadora_periodo (operadora_id, ano, trimestre),
    INDEX idx_ano_trimestre (ano, trimestre),
    INDEX idx_valor (valor_despesas),
    INDEX idx_periodo (ano, trimestre, operadora_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Despesas com eventos/sinistros por operadora e trimestre';

-- ============================================================================
-- TABELA: despesas_agregadas
-- Armazena dados agregados pré-calculados para melhor performance
-- ============================================================================

CREATE TABLE despesas_agregadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operadora_id INT NOT NULL,
    total_despesas DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    media_por_trimestre DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    desvio_padrao DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    numero_trimestres INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (operadora_id) REFERENCES operadoras(id) ON DELETE CASCADE,
    UNIQUE KEY uk_operadora (operadora_id),
    INDEX idx_total_despesas (total_despesas DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Dados agregados de despesas por operadora';

-- ============================================================================
-- VIEWS AUXILIARES
-- ============================================================================

CREATE VIEW vw_despesas_completas AS
SELECT 
    d.id,
    o.cnpj,
    o.razao_social,
    o.uf,
    o.modalidade,
    d.ano,
    d.trimestre,
    d.valor_despesas,
    CONCAT(d.ano, '-Q', d.trimestre) AS periodo
FROM despesas d
INNER JOIN operadoras o ON d.operadora_id = o.id;

CREATE VIEW vw_resumo_operadoras AS
SELECT 
    o.id,
    o.cnpj,
    o.razao_social,
    o.uf,
    o.modalidade,
    COALESCE(da.total_despesas, 0) AS total_despesas,
    COALESCE(da.media_por_trimestre, 0) AS media_por_trimestre,
    COALESCE(da.numero_trimestres, 0) AS numero_trimestres
FROM operadoras o
LEFT JOIN despesas_agregadas da ON o.id = da.operadora_id;

-- ============================================================================
-- TRIGGERS DE NORMALIZAÇÃO AUTOMÁTICA
-- ============================================================================

DELIMITER $$

-- Trigger para normalizar dados ANTES de INSERT
CREATE TRIGGER normalize_operadora_before_insert
BEFORE INSERT ON operadoras
FOR EACH ROW
BEGIN
    -- Normalizar CNPJ: remove formatação e valida 14 dígitos exatos
    IF NEW.cnpj IS NOT NULL THEN
        -- Remover formatação (pontos, barras, traços)
        SET NEW.cnpj = REPLACE(REPLACE(REPLACE(NEW.cnpj, '.', ''), '/', ''), '-', '');
        -- Se não tiver exatamente 14 dígitos = inválido
        IF LENGTH(NEW.cnpj) != 14 THEN
            SET NEW.cnpj = NULL;
        END IF;
    END IF;
    
    -- Normalizar encoding da razão social
    IF NEW.razao_social IS NOT NULL THEN
        SET NEW.razao_social = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            REPLACE(REPLACE(REPLACE(REPLACE(
            NEW.razao_social,
            'Ãº', 'ú'), 'Ã³', 'ó'), 'Ã­', 'í'), 'Ã©', 'é'), 'Ã¡', 'á'),
            'Ãª', 'ê'), 'Ã´', 'ô'), 'Ã£', 'ã'), 'Ã§', 'ç'), 'Ã', 'Ã');
    END IF;
    
    -- Normalizar encoding da modalidade
    IF NEW.modalidade IS NOT NULL THEN
        SET NEW.modalidade = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            REPLACE(REPLACE(REPLACE(REPLACE(
            NEW.modalidade,
            'Ãº', 'ú'), 'Ã³', 'ó'), 'Ã­', 'í'), 'Ã©', 'é'), 'Ã¡', 'á'),
            'Ãª', 'ê'), 'Ã´', 'ô'), 'Ã£', 'ã'), 'Ã§', 'ç'), 'Ã', 'Ã');
    END IF;
    
    -- Limpar UF corrompido (mais de 2 caracteres = inválido)
    IF NEW.uf IS NOT NULL AND LENGTH(NEW.uf) > 2 THEN
        SET NEW.uf = NULL;
    END IF;
END$$

-- Trigger para normalizar dados ANTES de UPDATE
CREATE TRIGGER normalize_operadora_before_update
BEFORE UPDATE ON operadoras
FOR EACH ROW
BEGIN
    -- Normalizar CNPJ: remove formatação e valida 14 dígitos exatos
    IF NEW.cnpj IS NOT NULL THEN
        -- Remover formatação (pontos, barras, traços)
        SET NEW.cnpj = REPLACE(REPLACE(REPLACE(NEW.cnpj, '.', ''), '/', ''), '-', '');
        -- Se não tiver exatamente 14 dígitos = inválido
        IF LENGTH(NEW.cnpj) != 14 THEN
            SET NEW.cnpj = NULL;
        END IF;
    END IF;
    
    -- Normalizar encoding da razão social
    IF NEW.razao_social IS NOT NULL THEN
        SET NEW.razao_social = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            REPLACE(REPLACE(REPLACE(REPLACE(
            NEW.razao_social,
            'Ãº', 'ú'), 'Ã³', 'ó'), 'Ã­', 'í'), 'Ã©', 'é'), 'Ã¡', 'á'),
            'Ãª', 'ê'), 'Ã´', 'ô'), 'Ã£', 'ã'), 'Ã§', 'ç'), 'Ã', 'Ã');
    END IF;
    
    -- Normalizar encoding da modalidade
    IF NEW.modalidade IS NOT NULL THEN
        SET NEW.modalidade = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            REPLACE(REPLACE(REPLACE(REPLACE(
            NEW.modalidade,
            'Ãº', 'ú'), 'Ã³', 'ó'), 'Ã­', 'í'), 'Ã©', 'é'), 'Ã¡', 'á'),
            'Ãª', 'ê'), 'Ã´', 'ô'), 'Ã£', 'ã'), 'Ã§', 'ç'), 'Ã', 'Ã');
    END IF;
    
    -- Limpar UF corrompido (mais de 2 caracteres = inválido)
    IF NEW.uf IS NOT NULL AND LENGTH(NEW.uf) > 2 THEN
        SET NEW.uf = NULL;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- JUSTIFICATIVAS TÉCNICAS
-- ============================================================================

/*
DECISÃO 1: NORMALIZAÇÃO
- Estrutura semi-normalizada com 3 tabelas principais
- operadoras: Dados cadastrais (evita duplicação de razão social, UF, etc.)
- despesas: Dados transacionais de despesas
- despesas_agregadas: Cache de agregações (pré-calculado para performance)

Justificativa:
- Volume esperado: ~10k operadoras, ~30k registros de despesas
- Frequência de atualização: Trimestral (baixa)
- Queries analíticas: Frequentes e complexas
- Trade-off: Normalização reduz redundância mas requer JOINs. Para volume pequeno/médio
  e atualizações raras, normalização é ideal.

DECISÃO 2: TIPOS DE DADOS
- CNPJ: CHAR(14) - Tamanho fixo, melhor performance em índices
- Valores: DECIMAL(15,2) - Precisão exata para valores monetários (evita erros de arredondamento)
- Datas: Separado em ano (SMALLINT) + trimestre (TINYINT) - Facilita queries trimestrais
- Strings: VARCHAR com utf8mb4_unicode_ci - Suporte completo a caracteres especiais

Justificativa:
- DECIMAL vs FLOAT: Precisão necessária para valores financeiros
- CHAR vs VARCHAR para CNPJ: Tamanho fixo otimiza índices
- ano/trimestre separados vs DATE: Granularidade trimestral não necessita precisão diária

DECISÃO 3: ÍNDICES
- PRIMARY KEY em INT AUTO_INCREMENT (mais eficiente que CNPJ como PK)
- UNIQUE em CNPJ (garantir unicidade)
- INDEX em razao_social, uf, modalidade (campos de busca/filtro comuns)
- INDEX composto em (ano, trimestre, operadora_id) (queries temporais)
- INDEX em valor_despesas (ordenação por valor)

Justificativa:
- AUTO_INCREMENT PK: Melhor performance para JOINs e menor tamanho de índice
- Índices em campos de filtro: 80% das queries filtram por UF ou modalidade
- Índice composto temporal: Queries de crescimento e análise trimestral são frequentes

DECISÃO 4: ENGINE E CHARSET
- InnoDB: Suporte a transações, foreign keys e melhor performance para leitura/escrita
- utf8mb4_unicode_ci: Suporte completo a caracteres Unicode (nomes com acentos)

DECISÃO 5: VIEWS
- Criadas para simplificar queries frequentes
- vw_despesas_completas: Evita repetir JOINs em queries analíticas
- vw_resumo_operadoras: Facilita listagem com totais
*/
