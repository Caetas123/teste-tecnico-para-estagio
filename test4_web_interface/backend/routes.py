from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models import Operadora, DespesaCompleta, Estatisticas, PaginatedResponse
from database import Database
import time
from decimal import Decimal
import math

router = APIRouter()


cache = {}
CACHE_TTL = 300

def get_cached(key: str):
    if key in cache:
        cached_data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return cached_data
        else:
            del cache[key]
    return None

def set_cache(key: str, data):
    cache[key] = (data, time.time())

@router.get("/api/operadoras", response_model=PaginatedResponse)
async def get_operadoras(
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    busca: Optional[str] = Query(None, description="Busca por razão social ou CNPJ")
):
    offset = (page - 1) * limit
    
    base_query = """
        SELECT 
            o.id,
            o.cnpj,
            o.razao_social,
            o.registro_ans,
            o.modalidade,
            o.uf,
            COALESCE(da.total_despesas, 0) AS total_despesas,
            COALESCE(da.media_por_trimestre, 0) AS media_por_trimestre,
            COALESCE(da.numero_trimestres, 0) AS numero_trimestres
        FROM operadoras o
        LEFT JOIN despesas_agregadas da ON o.id = da.operadora_id
    """
    
    count_query = """
        SELECT COUNT(*) AS total
        FROM operadoras o
    """
    
    where_clause = ""
    params = []
    
    if busca:
        # Padronizar CNPJ se a busca for numérica (remover formatação)
        busca_cnpj = busca.strip()
        # Remover caracteres de formatação de CNPJ (pontos, barras, traços)
        busca_cnpj_limpo = busca_cnpj.replace('.', '').replace('/', '').replace('-', '')
        if busca_cnpj_limpo.isdigit():
            busca_cnpj = busca_cnpj_limpo.zfill(14)
        
        # Busca simples - dados já estão normalizados no banco
        where_clause = " WHERE o.razao_social LIKE %s OR o.cnpj LIKE %s"
        search_param_texto = f"%{busca}%"
        search_param_cnpj = f"%{busca_cnpj}%"
        params = [search_param_texto, search_param_cnpj]
    
    query = base_query + where_clause + " ORDER BY total_despesas DESC LIMIT %s OFFSET %s"
    count_query = count_query + where_clause
    
    params_query = params + [limit, offset]
    params_count = tuple(params) if params else ()
    
    try:
        results, total = Database.execute_query_with_count(
            query,
            count_query,
            tuple(params_query),
            params_count
        )
        
        for row in results:
            if isinstance(row.get('total_despesas'), Decimal):
                row['total_despesas'] = float(row['total_despesas'])
            if isinstance(row.get('media_por_trimestre'), Decimal):
                row['media_por_trimestre'] = float(row['media_por_trimestre'])
            # Dados já estão normalizados no banco - não precisa mais corrigir encoding
        
        total_pages = math.ceil(total / limit) if total > 0 else 0
        
        return PaginatedResponse(
            data=results,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/operadoras/{cnpj}", response_model=dict)
async def get_operadora_by_cnpj(cnpj: str):
    # Padronizar CNPJ para 14 dígitos antes de buscar (remover formatação)
    cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
    cnpj_padronizado = cnpj_limpo.zfill(14)
    
    query = """
        SELECT 
            o.id,
            o.cnpj,
            o.razao_social,
            o.registro_ans,
            o.modalidade,
            o.uf,
            COALESCE(da.total_despesas, 0) AS total_despesas,
            COALESCE(da.media_por_trimestre, 0) AS media_por_trimestre,
            COALESCE(da.desvio_padrao, 0) AS desvio_padrao,
            COALESCE(da.numero_trimestres, 0) AS numero_trimestres
        FROM operadoras o
        LEFT JOIN despesas_agregadas da ON o.id = da.operadora_id
        WHERE o.cnpj = %s
    """
    
    try:
        results = Database.execute_query(query, (cnpj_padronizado,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Operadora não encontrada")
        
        operadora = results[0]
        
        
        if isinstance(operadora.get('total_despesas'), Decimal):
            operadora['total_despesas'] = float(operadora['total_despesas'])
        if isinstance(operadora.get('media_por_trimestre'), Decimal):
            operadora['media_por_trimestre'] = float(operadora['media_por_trimestre'])
        if isinstance(operadora.get('desvio_padrao'), Decimal):
            operadora['desvio_padrao'] = float(operadora['desvio_padrao'])
        
        return operadora
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/operadoras/{cnpj}/despesas")
async def get_despesas_operadora(cnpj: str):
    # Padronizar CNPJ para 14 dígitos antes de buscar (remover formatação)
    cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
    cnpj_padronizado = cnpj_limpo.zfill(14)
    
    query = """
        SELECT 
            d.id,
            d.operadora_id,
            d.ano,
            d.trimestre,
            d.valor_despesas,
            CONCAT(d.ano, '-Q', d.trimestre) AS periodo
        FROM despesas d
        INNER JOIN operadoras o ON d.operadora_id = o.id
        WHERE o.cnpj = %s
        ORDER BY d.ano, d.trimestre
    """
    
    try:
        results = Database.execute_query(query, (cnpj_padronizado,))
        
        for row in results:
            if isinstance(row.get('valor_despesas'), Decimal):
                row['valor_despesas'] = float(row['valor_despesas'])
        
        return {
            "cnpj": cnpj_padronizado,
            "despesas": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/estatisticas", response_model=dict)
async def get_estatisticas():
    cached_data = get_cached("estatisticas")
    if cached_data:
        return cached_data
    
    try:
        total_operadoras_query = "SELECT COUNT(*) AS total FROM operadoras"
        total_operadoras = Database.execute_query(total_operadoras_query)[0]['total']
        
        total_despesas_query = "SELECT SUM(valor_despesas) AS total FROM despesas"
        total_despesas_result = Database.execute_query(total_despesas_query)[0]
        total_despesas = float(total_despesas_result['total']) if total_despesas_result['total'] else 0.0
        
        media_query = "SELECT AVG(valor_despesas) AS media FROM despesas"
        media_result = Database.execute_query(media_query)[0]
        media_despesas = float(media_result['media']) if media_result['media'] else 0.0
        
        top5_query = """
            SELECT 
                o.cnpj,
                o.razao_social,
                o.uf,
                da.total_despesas
            FROM despesas_agregadas da
            INNER JOIN operadoras o ON da.operadora_id = o.id
            ORDER BY da.total_despesas DESC
            LIMIT 5
        """
        top5_results = Database.execute_query(top5_query)
        
        for row in top5_results:
            if isinstance(row.get('total_despesas'), Decimal):
                row['total_despesas'] = float(row['total_despesas'])
            # Dados já normalizados via triggers do banco
        
        distribuicao_uf_query = """
            SELECT 
                o.uf,
                SUM(d.valor_despesas) AS total_despesas,
                COUNT(DISTINCT o.id) AS total_operadoras
            FROM despesas d
            INNER JOIN operadoras o ON d.operadora_id = o.id
            WHERE o.uf IS NOT NULL AND o.uf <> '' AND LENGTH(o.uf) = 2
            GROUP BY o.uf
            ORDER BY total_despesas DESC
            LIMIT 10
        """
        distribuicao_results = Database.execute_query(distribuicao_uf_query)
        
        for row in distribuicao_results:
            if isinstance(row.get('total_despesas'), Decimal):
                row['total_despesas'] = float(row['total_despesas'])
        
        result = {
            "total_operadoras": total_operadoras,
            "total_despesas": total_despesas,
            "media_despesas": media_despesas,
            "top_5_operadoras": top5_results,
            "distribuicao_uf": distribuicao_results
        }
        
        set_cache("estatisticas", result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
