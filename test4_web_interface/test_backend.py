import sys
import requests
import time
from pathlib import Path

def test_api():
    base_url = "http://localhost:8000"
    
    print("="*80)
    print("TESTE 4: API E INTERFACE WEB")
    print("="*80)
    print("\nTestando endpoints da API...\n")
    
    tests = []
    
    # Test 1: Health check
    print("1. GET /health")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            tests.append(("Health Check", True))
        else:
            print(f"   ✗ Status: {response.status_code}")
            tests.append(("Health Check", False))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        tests.append(("Health Check", False))
    
    print()
    
    # Test 2: Root endpoint
    print("2. GET /")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Status: {response.status_code}")
            data = response.json()
            print(f"   API: {data.get('message')}")
            tests.append(("Root Endpoint", True))
        else:
            print(f"   ✗ Status: {response.status_code}")
            tests.append(("Root Endpoint", False))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        tests.append(("Root Endpoint", False))
    
    print()
    
    # Test 3: List operadoras
    print("3. GET /api/operadoras?page=1&limit=5")
    try:
        response = requests.get(f"{base_url}/api/operadoras?page=1&limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Status: {response.status_code}")
            print(f"   Total: {data.get('total')} operadoras")
            print(f"   Página: {data.get('page')}/{data.get('total_pages')}")
            print(f"   Registros: {len(data.get('data', []))}")
            if data.get('data'):
                print(f"   Exemplo: {data['data'][0].get('razao_social')}")
            tests.append(("List Operadoras", True))
        else:
            print(f"   ✗ Status: {response.status_code}")
            tests.append(("List Operadoras", False))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        tests.append(("List Operadoras", False))
    
    print()
    
    # Test 4: Get estatísticas
    print("4. GET /api/estatisticas")
    try:
        response = requests.get(f"{base_url}/api/estatisticas", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Status: {response.status_code}")
            print(f"   Total Operadoras: {data.get('total_operadoras')}")
            print(f"   Total Despesas: R$ {data.get('total_despesas', 0):,.2f}")
            print(f"   Média Despesas: R$ {data.get('media_despesas', 0):,.2f}")
            if data.get('top_5_operadoras'):
                print(f"   Top 5 disponível: {len(data['top_5_operadoras'])} operadoras")
            tests.append(("Estatísticas", True))
        else:
            print(f"   ✗ Status: {response.status_code}")
            tests.append(("Estatísticas", False))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        tests.append(("Estatísticas", False))
    
    print()
    
    # Test 5: Get specific operadora (usando CNPJ da primeira operadora)
    print("5. GET /api/operadoras/{cnpj}")
    try:
        # Primeiro, pegar um CNPJ válido
        response = requests.get(f"{base_url}/api/operadoras?page=1&limit=1", timeout=5)
        if response.status_code == 200 and response.json().get('data'):
            cnpj = response.json()['data'][0]['cnpj']
            
            response = requests.get(f"{base_url}/api/operadoras/{cnpj}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Status: {response.status_code}")
                print(f"   CNPJ: {data.get('cnpj')}")
                print(f"   Razão Social: {data.get('razao_social')}")
                print(f"   UF: {data.get('uf')}")
                tests.append(("Get Operadora", True))
            else:
                print(f"   ✗ Status: {response.status_code}")
                tests.append(("Get Operadora", False))
        else:
            print("   Aviso: Nenhuma operadora disponível para teste")
            tests.append(("Get Operadora", None))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        tests.append(("Get Operadora", False))
    
    print()
    
    # Test 6: Get despesas da operadora
    print("6. GET /api/operadoras/{cnpj}/despesas")
    try:
        response = requests.get(f"{base_url}/api/operadoras?page=1&limit=1", timeout=5)
        if response.status_code == 200 and response.json().get('data'):
            cnpj = response.json()['data'][0]['cnpj']
            
            response = requests.get(f"{base_url}/api/operadoras/{cnpj}/despesas", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Status: {response.status_code}")
                print(f"   Total despesas: {data.get('total_registros')}")
                if data.get('despesas'):
                    print(f"   Registros retornados: {len(data['despesas'])}")
                    primeiro = data['despesas'][0]
                    print(f"   Exemplo: {primeiro.get('ano')}-Q{primeiro.get('trimestre')} = R$ {primeiro.get('valor_despesas', 0):,.2f}")
                tests.append(("Get Despesas", True))
            else:
                print(f"   ✗ Status: {response.status_code}")
                tests.append(("Get Despesas", False))
        else:
            print("   Aviso: Nenhuma operadora disponível para teste")
            tests.append(("Get Despesas", None))
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        tests.append(("Get Despesas", False))
    
    print()
    print("="*80)
    print("RESUMO DOS TESTES")
    print("="*80)
    
    passed = sum(1 for _, result in tests if result is True)
    failed = sum(1 for _, result in tests if result is False)
    skipped = sum(1 for _, result in tests if result is None)
    
    for test_name, result in tests:
        status = "PASSOU" if result is True else ("FALHOU" if result is False else "PULADO")
        print(f"{test_name}: {status}")
    
    print()
    print(f"Total: {len(tests)} testes")
    print(f"Passaram: {passed}")
    print(f"Falharam: {failed}")
    print(f"Pulados: {skipped}")
    
    if failed == 0 and passed > 0:
        print("\n✓ TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("\n✗ ALGUNS TESTES FALHARAM")
        return False

if __name__ == "__main__":
    print("Aguardando servidor iniciar...")
    time.sleep(2)
    
    try:
        success = test_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTestes interrompidos pelo usuário")
        sys.exit(1)
