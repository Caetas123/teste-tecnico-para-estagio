# Data

Dados de entrada do projeto.

## Estrutura

```
data/
├── operadoras_ativas.csv
├── operadoras_cadastro.csv
├── 1T2025/
│   └── 1T2025.csv
├── 2T2025/
│   └── 2T2025.csv
└── 3T2025/
    └── 3T2025.csv
```

## Obter os Dados

### Opção 1: Download Automático

```powershell
cd test1_api_integration
python main.py
```

O script baixa automaticamente os 3 trimestres mais recentes da API da ANS.

### Opção 2: Download Manual

1. Acesse: https://dadosabertos.ans.gov.br/FTP/PDA/
2. Navegue até os diretórios dos trimestres
3. Baixe os arquivos ZIP
4. Extraia na estrutura acima

Dados cadastrais: https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/
