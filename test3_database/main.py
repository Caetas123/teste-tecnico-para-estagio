import mysql.connector
import pandas as pd
from pathlib import Path
import sys

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'charset': 'utf8mb4',
            'allow_local_infile': True
        }
        self.connection = None
        self.cursor = None
    
    def connect(self):
        print("Conectando ao MySQL...")
        
        # Tentar diferentes configurações comuns
        configs_to_try = [
            {'port': 3306, 'password': ''},        # MySQL padrão
            {'port': 3307, 'password': ''},        # WAMP alternativo
            {'port': 3306, 'password': 'root'},    # Senha comum
        ]
        
        for config_override in configs_to_try:
            try:
                test_config = self.config.copy()
                test_config.update(config_override)
                
                print(f"Tentando porta {test_config['port']}...", end=' ')
                self.connection = mysql.connector.connect(**test_config)
                self.cursor = self.connection.cursor()
                self.config = test_config
                print("✓ Conectado!")
                return True
            except mysql.connector.Error:
                print("✗")
                continue
        
        print("\nErro: Não foi possível conectar ao MySQL")
        print("\nVerifique:")
        print("1. MySQL/WAMP está rodando")
        print("   - WAMP: Inicie o WAMP e clique em 'Start All Services'")
        print("   - MySQL80: net start MySQL80 (como Administrador)")
        print("2. Usuário: root")
        print("3. Senha: (vazia ou 'root')")
        print("4. Porta: 3306 ou 3307")
        return False
    
    def execute_sql_file(self, filepath: Path):
        print(f"\nExecutando: {filepath.name}")
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        statements = []
        current = []
        in_delimiter = False
        
        for line in sql_content.split('\n'):
            line_stripped = line.strip()
            
            if line_stripped.startswith('--') or not line_stripped:
                continue
            
            if 'DELIMITER' in line_stripped.upper():
                in_delimiter = not in_delimiter
                continue
            
            current.append(line)
            
            if not in_delimiter and line_stripped.endswith(';'):
                statements.append('\n'.join(current))
                current = []
        
        if current:
            statements.append('\n'.join(current))
        
        for i, statement in enumerate(statements, 1):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
            
            try:
                # Usar connection.execute para multi-statement
                results = self.connection.cmd_query(statement)
                self.connection.commit()
            except mysql.connector.Error as e:
                if 'database exists' not in str(e).lower() and 'already exists' not in str(e).lower():
                    print(f"Aviso: {e}")
        
        print(f"✓ {filepath.name} executado com sucesso")
    
    def import_csv_data(self):
        print("\nImportando dados dos CSVs...")
        
        self.cursor.execute("USE ans_database")
        
        consolidado_path = Path('output/consolidado_enriquecido.csv')
        if not consolidado_path.exists():
            print(f"Erro: {consolidado_path} não encontrado")
            return False
        
        df = pd.read_csv(consolidado_path)
        print(f"Carregado: {len(df)} registros")
        
        df['CNPJ'] = df['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
        df['RazaoSocial'] = df['RazaoSocial'].fillna('NÃO IDENTIFICADO')
        df['RegistroANS'] = df['RegistroANS'].fillna('')
        df['Modalidade'] = df['Modalidade'].fillna('NÃO IDENTIFICADO')
        df['UF'] = df['UF'].fillna('XX')
        
        operadoras_map = {}
        inserted = 0
        
        for _, row in df.iterrows():
            cnpj = row['CNPJ']
            
            if cnpj not in operadoras_map:
                try:
                    self.cursor.execute("""
                        INSERT IGNORE INTO operadoras (cnpj, razao_social, registro_ans, modalidade, uf)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (cnpj, row['RazaoSocial'], row['RegistroANS'], row['Modalidade'], row['UF']))
                    
                    self.cursor.execute("SELECT id FROM operadoras WHERE cnpj = %s", (cnpj,))
                    result = self.cursor.fetchone()
                    if result:
                        operadoras_map[cnpj] = result[0]
                        inserted += 1
                except mysql.connector.Error as e:
                    print(f"Erro ao inserir operadora {cnpj}: {e}")
                    continue
        
        self.connection.commit()
        print(f"✓ Operadoras inseridas: {inserted}")
        
        despesas_inserted = 0
        for _, row in df.iterrows():
            cnpj = row['CNPJ']
            if cnpj in operadoras_map:
                try:
                    self.cursor.execute("""
                        INSERT IGNORE INTO despesas (operadora_id, ano, trimestre, valor_despesas)
                        VALUES (%s, %s, %s, %s)
                    """, (operadoras_map[cnpj], int(row['Ano']), int(row['Trimestre']), float(row['ValorDespesas'])))
                    despesas_inserted += self.cursor.rowcount
                except mysql.connector.Error as e:
                    print(f"Erro ao inserir despesa: {e}")
        
        self.connection.commit()
        print(f"✓ Despesas inseridas: {despesas_inserted}")
        
        agregadas_path = Path('output/despesas_agregadas.csv')
        if agregadas_path.exists():
            df_agg = pd.read_csv(agregadas_path)
            print(f"\nImportando dados agregados: {len(df_agg)} registros")
            
            agg_inserted = 0
            for _, row in df_agg.iterrows():
                razao = row['RazaoSocial']
                
                self.cursor.execute("SELECT id FROM operadoras WHERE razao_social = %s LIMIT 1", (razao,))
                result = self.cursor.fetchone()
                
                if result:
                    try:
                        self.cursor.execute("""
                            INSERT IGNORE INTO despesas_agregadas 
                            (operadora_id, total_despesas, media_por_trimestre, desvio_padrao, numero_trimestres)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (result[0], float(row['TotalDespesas']), float(row['MediaPorTrimestre']), 
                             float(row['DesvioPadrao']), int(row['NumeroTrimestres'])))
                        agg_inserted += self.cursor.rowcount
                    except mysql.connector.Error as e:
                        print(f"Erro ao inserir agregado: {e}")
            
            self.connection.commit()
            print(f"✓ Agregados inseridos: {agg_inserted}")
        
        return True
    
    def execute_queries(self):
        print("\n" + "="*80)
        print("EXECUTANDO QUERIES ANALÍTICAS")
        print("="*80)
        
        queries_path = Path('test3_database/queries.sql')
        if not queries_path.exists():
            print("Arquivo queries.sql não encontrado")
            return
        
        with open(queries_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Dividir por queries separadas por comentários
        queries_dict = {
            'Query 1: Top 5 operadoras com maior crescimento percentual': None,
            'Query 2: Distribuição de despesas por UF (Top 5 estados)': None,
            'Query 3: Operadoras com despesas acima da média em 2+ trimestres': None
        }
        
        current_query = []
        current_title = None
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # Detectar início de nova query
            if 'QUERY 1' in stripped.upper() and 'TOP 5' in stripped.upper():
                current_title = 'Query 1: Top 5 operadoras com maior crescimento percentual'
                current_query = []
            elif 'QUERY 2' in stripped.upper() and 'DISTRIBUIÇÃO' in stripped.upper():
                if current_title and current_query:
                    queries_dict[current_title] = '\n'.join(current_query)
                current_title = 'Query 2: Distribuição de despesas por UF (Top 5 estados)'
                current_query = []
            elif 'QUERY 3' in stripped.upper() and 'ACIMA DA MÉDIA' in stripped.upper():
                if current_title and current_query:
                    queries_dict[current_title] = '\n'.join(current_query)
                current_title = 'Query 3: Operadoras com despesas acima da média em 2+ trimestres'
                current_query = []
            elif not stripped.startswith('--') and stripped and current_title:
                current_query.append(line)
        
        if current_title and current_query:
            queries_dict[current_title] = '\n'.join(current_query)
        
        results_file = Path('output/resultados_queries.txt')
        with open(results_file, 'w', encoding='utf-8') as f:
            for title, query in queries_dict.items():
                if not query or not query.strip():
                    continue
                
                print(f"\n{title}")
                print("-" * 80)
                f.write(f"\n{'='*80}\n{title}\n{'='*80}\n\n")
                
                try:
                    # Garantir conexão ativa
                    if not self.connection.is_connected():
                        self.connection.reconnect()
                    
                    # Criar novo cursor para cada query
                    query_cursor = self.connection.cursor()
                    query_cursor.execute("USE ans_database")
                    query_cursor.execute(query)
                    
                    results = query_cursor.fetchall()
                    
                    if query_cursor.description:
                        columns = [desc[0] for desc in query_cursor.description]
                        df = pd.DataFrame(results, columns=columns)
                        
                        print(df.to_string(index=False))
                        f.write(df.to_string(index=False))
                        f.write('\n\n')
                    else:
                        print("Query executada com sucesso (sem resultados)")
                        f.write("Query executada com sucesso\n\n")
                    
                    query_cursor.close()
                    
                except mysql.connector.Error as e:
                    error_msg = f"Erro: {e}"
                    print(error_msg)
                    f.write(error_msg + '\n\n')
        
        print(f"\n✓ Resultados salvos em: {results_file}")
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("\nConexão fechada")

def main():
    print("="*80)
    print("TESTE 3: BANCO DE DADOS E ANÁLISE - MySQL 8.0")
    print("="*80)
    print("\nDica: Se usar WAMP, inicie os serviços antes de executar este script")
    print()
    
    db = DatabaseManager()
    
    if not db.connect():
        sys.exit(1)
    
    try:
        schema_path = Path('test3_database/schema.sql')
        db.execute_sql_file(schema_path)
        
        if not db.import_csv_data():
            print("Erro na importação de dados")
            sys.exit(1)
        
        db.execute_queries()
        
        print("\n" + "="*80)
        print("TESTE 3 CONCLUÍDO COM SUCESSO!")
        print("="*80)
        print("\nArquivos gerados:")
        print("  - output/resultados_queries.txt")
        print("\nBanco de dados 'ans_database' criado e populado")
        
    except Exception as e:
        print(f"\nErro durante execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
