from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class Operadora(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    registro_ans: Optional[str] = None
    modalidade: Optional[str] = None
    uf: Optional[str] = None
    total_despesas: Optional[Decimal] = None
    media_por_trimestre: Optional[Decimal] = None
    numero_trimestres: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }

class Despesa(BaseModel):
    id: int
    operadora_id: int
    ano: int
    trimestre: int
    valor_despesas: Decimal
    periodo: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }

class DespesaCompleta(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    uf: Optional[str]
    modalidade: Optional[str]
    ano: int
    trimestre: int
    valor_despesas: Decimal
    periodo: str
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }

class Estatisticas(BaseModel):
    total_operadoras: int
    total_despesas: Decimal
    media_despesas: Decimal
    top_5_operadoras: List[dict]
    distribuicao_uf: List[dict]
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }

class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    page: int
    limit: int
    total_pages: int
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else 0.0
        }
