import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict
import time
from config.settings import ANS_API_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF_FACTOR

class ANSApiClient:
    def __init__(self):
        self.base_url = ANS_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _request_with_retry(self, url: str, stream: bool = False) -> requests.Response:
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=stream)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                wait_time = RETRY_BACKOFF_FACTOR ** attempt
                print(f"Tentativa {attempt + 1} falhou. Aguardando {wait_time}s...")
                time.sleep(wait_time)
    
    def get_available_quarters(self, num_quarters: int = 3) -> List[Dict[str, str]]:
        print("Identificando trimestres disponíveis...")
        
        url = f"{self.base_url}demonstracoes_contabeis/"
        response = self._request_with_retry(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        years = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href and href.endswith('/') and href[:-1].isdigit():
                year = int(href[:-1])
                if year >= 2020:
                    years.append(year)
        
        years = sorted(years, reverse=True)
        
        quarters_found = []
        for year in years:
            if len(quarters_found) >= num_quarters:
                break
            
            year_url = f"{url}{year}/"
            try:
                response = self._request_with_retry(year_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                year_quarters = []
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    # Procurar por arquivos ZIP de trimestre (1T2024.zip, 2T2024.zip, etc)
                    if href.endswith('.zip') and any(href.startswith(q) for q in ['1T', '2T', '3T', '4T']):
                        quarter_num = int(href[0])
                        year_quarters.append({
                            'year': year,
                            'quarter': quarter_num,
                            'url': f"{year_url}{href}"
                        })
                
                year_quarters = sorted(year_quarters, key=lambda x: x['quarter'], reverse=True)
                quarters_found.extend(year_quarters)
                
                if len(quarters_found) >= num_quarters:
                    quarters_found = quarters_found[:num_quarters]
                    break
                    
            except Exception as e:
                print(f"Erro ao processar ano {year}: {e}")
                continue
        
        print(f"Encontrados {len(quarters_found)} trimestres")
        return quarters_found
    
    def get_expense_files(self, quarter_url: str) -> List[str]:
        # A URL já é o arquivo ZIP direto (ex: https://.../3T2025.zip)
        return [quarter_url]
    
    def download_file(self, url: str, destination: Path) -> bool:
        try:
            print(f"Baixando: {url}")
            response = self._request_with_retry(url, stream=True)
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"Progresso: {progress:.1f}%", end='\r')
            
            print(f"\nArquivo salvo: {destination}")
            return True
        except Exception as e:
            print(f"Erro ao baixar {url}: {e}")
            return False
