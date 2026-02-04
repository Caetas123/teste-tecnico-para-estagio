# Teste Técnico - Análise de Dados ANS
Candidato: Caetano Matarazo Granado

Solução completa em 4 testes: integração com API, transformação de dados, SQL e interface web.

## Estrutura do Projeto

```
estagio2/
├── config/                      # Configurações globais
│   ├── settings.py             # Caminhos e constantes
│   └── __init__.py
│
├── data/                        # Dados de entrada (CSVs da ANS)
│   ├── operadoras_ativas.csv   # Dados cadastrais
│   ├── 1T2025/, 2T2025/, 3T2025/ # Dados de trimestres
│
├── output/                      # Arquivos gerados (CSVs e logs)
│   ├── consolidado_despesas.csv
│   ├── consolidado_enriquecido.csv
│   ├── despesas_agregadas.csv
│   └── *.log / *.txt
│
├── test1_api_integration/       # TESTE 1: API ANS
│   ├── main.py                 # Executável principal
│   ├── api_client.py           # Cliente HTTP
│   ├── file_processor.py       # Processamento de arquivos
│   ├── data_consolidator.py    # Consolidação de dados
│   ├── cadastral_data.py       # Enriquecimento cadastral
│   └── README.md               # Documentação detalhada
│
├── test2_data_transformation/   # TESTE 2: Transformação
│   ├── main.py                 # Executável principal
│   ├── validators.py           # Validação de dados
│   ├── data_enrichment.py      # Enriquecimento
│   ├── aggregator.py           # Agregação
│   └── README.md               # Documentação detalhada
│
├── test3_database/              # TESTE 3: Banco de Dados
│   ├── schema.sql              # Criação de tabelas
│   ├── import_data.sql         # Importação de CSVs
│   ├── queries.sql             # Queries analíticas
│   ├── main.py                 # Script Python auxiliar
│   └── README.md               # Documentação detalhada
│
├── test4_web_interface/         # TESTE 4: Interface Web
│   ├── backend/                # API REST (FastAPI)
│   │   ├── app.py              # Aplicação principal
│   │   ├── routes.py           # Rotas da API
│   │   ├── models.py           # Modelos de dados
│   │   ├── database.py         # Conexão com BD
│   │   └── postman_collection.json
│   ├── frontend/               # Interface Vue.js
│   │   ├── src/
│   │   │   ├── App.vue
│   │   │   ├── components/
│   │   │   ├── router/
│   │   │   └── services/
│   │   ├── package.json
│   │   └── vite.config.js
│   └── README.md               # Documentação detalhada
│
├── requirements.txt             # Dependências Python
└── README.md                    # Este arquivo
```

## Como Executar

### Pré-requisitos

- Python 3.8+
- Node.js 16+ e npm
- MySQL 8.0
- Git

### Passo 1: Configurar Ambiente Python

```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### Passo 2: Executar os Testes

#### TESTE 1 - Integração com API ANS

```powershell
cd test1_api_integration
python main.py
```

**Saída esperada:**
- `output/consolidado_despesas.csv` - Dados consolidados
- `output/consolidado_despesas.zip` - Arquivo compactado
- `output/inconsistencias_log.txt` - Log de tratamento de dados

**Documentação completa:** [test1_api_integration/README.md](test1_api_integration/README.md)

---

#### TESTE 2 - Transformação e Validação de Dados

```powershell
cd test2_data_transformation
python main.py
```

**Saída esperada:**
- `output/consolidado_enriquecido.csv` - Dados validados e enriquecidos
- `output/despesas_agregadas.csv` - Dados agregados
- `output/validacao_log.txt` - Log de validação
- `output/enriquecimento_log.txt` - Log de enriquecimento

**Documentação completa:** [test2_data_transformation/README.md](test2_data_transformation/README.md)

---

#### TESTE 3 - Banco de Dados SQL

Criação do banco:
```bash
mysql -u root -p < test3_database/schema.sql
```

**Importação de dados:**
```bash
mysql -u root -p ans_database < test3_database/import_data.sql
```

**Executar queries analíticas:**
```bash
mysql -u root -p ans_database < test3_database/queries.sql
```

---

#### TESTE 4 - Interface Web

Backend (FastAPI):
```powershell
cd test4_web_interface\backend
python app.py
```

Servidor disponível em: `http://localhost:8000`  
Documentação da API: `http://localhost:8000/docs`

**Frontend (Vue.js):**
```bash
cd test4_web_interface/frontend
npm install
npm run dev
```

Interface disponível em: `http://localhost:5173`

**Documentação completa:** [test4_web_interface/README.md](test4_web_interface/README.md)

---

## Trade-offs Técnicos Documentados

Todos os trade-offs técnicos solicitados no teste foram documentados nos READMEs específicos de cada teste, incluindo:

### Teste 1
- Processamento em memória vs incremental
- Tratamento de inconsistências (CNPJs duplicados, valores negativos, etc.)

### Teste 2
- Estratégias de validação de CNPJ
- Métodos de join de dados
- Estratégias de ordenação

### Teste 3
- Normalização de banco de dados
- Tipos de dados (DECIMAL vs FLOAT vs INTEGER)
- Tratamento de importação de dados

### Teste 4
- Escolha do framework backend (FastAPI)
- Estratégia de paginação (offset-based)
- Cache vs queries diretas
- Gerenciamento de estado no frontend (Pinia)

## 📦 Como Gerar o ZIP Final

Para criar o arquivo de submissão:

```powershell
Compress-Archive -Path * -DestinationPath Teste_Caetano_Matarazo_Granado.zip
```

**O ZIP deve conter:**
- Código-fonte de todos os testes
- READMEs com documentação completa
- Arquivos de configuração (requirements.txt, package.json, etc.)
- Scripts SQL
- Coleção Postman
- Arquivos CSV gerados (consolidado e agregado)

## Observações Importantes

1. **Dados de Exemplo**: O diretório `data/` contém dados de exemplo para facilitar os testes. Em produção, os dados seriam baixados da API da ANS.

2. **Banco de Dados**: Para o teste 3, certifique-se de que o MySQL está rodando e que você tem permissões para criar databases.

3. **Dependências do Frontend**: A instalação do Node.js e npm é necessária apenas para o teste 4.

4. **Logs**: Todos os processos geram logs detalhados no diretório `output/` para auditoria e debugging.

## Tecnologias

- Python: Pandas, Requests, FastAPI, MySQL Connector
- JavaScript: Vue.js 3, Pinia, Chart.js, Axios
- SQL: MySQL 8.0

## Contato

Candidato: Caetano Matarazo Granado  
Vaga: Estágio
