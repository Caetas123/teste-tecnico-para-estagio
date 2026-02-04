#!/usr/bin/env python3
"""Script para testar as buscas da API"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_search(busca_termo):
    """Testa uma busca"""
    print(f"\n{'='*60}")
    print(f"Testando busca: '{busca_termo}'")
    print('='*60)
    
    response = requests.get(f"{BASE_URL}/api/operadoras", params={"busca": busca_termo})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Total encontrado: {data['total']}")
        print(f"✓ Resultados na página: {len(data['data'])}")
        
        if data['data']:
            print("\nPrimeiros resultados:")
            for i, item in enumerate(data['data'][:3], 1):
                print(f"\n  {i}. CNPJ: {item['cnpj']}")
                print(f"     Razão Social: {item['razao_social']}")
                print(f"     UF: {item.get('uf', 'N/A')}")
                print(f"     Total Despesas: R$ {item['total_despesas']:,.2f}")
        else:
            print("\nAviso: Nenhum resultado encontrado!")
    else:
        print(f"✗ Erro {response.status_code}: {response.text}")

def test_operadora_by_cnpj(cnpj):
    """Testa busca por CNPJ específico"""
    print(f"\n{'='*60}")
    print(f"Testando operadora por CNPJ: '{cnpj}'")
    print('='*60)
    
    response = requests.get(f"{BASE_URL}/api/operadoras/{cnpj}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"\nOperadora encontrada:")
        print(f"  CNPJ: {data['cnpj']}")
        print(f"  Razão Social: {data['razao_social']}")
        print(f"  Registro ANS: {data['registro_ans']}")
        print(f"  Modalidade: {data['modalidade']}")
        print(f"  UF: {data.get('uf', 'N/A')}")
        print(f"  Total Despesas: R$ {data['total_despesas']:,.2f}")
    else:
        print(f"✗ Erro {response.status_code}: {response.text}")

def main():
    print("\n" + "="*60)
    print("TESTE DE BUSCAS - API Operadoras ANS")
    print("="*60)
    
    # Teste 1: Busca por CNPJ sem zeros à esquerda (deve funcionar)
    test_search("1685053000156")
    
    # Teste 2: Busca por CNPJ com zeros à esquerda
    test_search("01685053000156")
    
    # Teste 3: Busca por parte do nome
    test_search("SAUDE")
    
    # Teste 4: Busca por nome completo
    test_search("UNIMED")
    
    # Teste 5: Busca direta por CNPJ (endpoint específico) - sem zeros
    test_operadora_by_cnpj("1685053000156")
    
    # Teste 6: Busca direta por CNPJ (endpoint específico) - com zeros
    test_operadora_by_cnpj("01685053000156")
    
    print("\n" + "="*60)
    print("TESTES CONCLUÍDOS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
