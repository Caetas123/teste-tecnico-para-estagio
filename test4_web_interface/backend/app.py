from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
import uvicorn

app = FastAPI(
    title="API ANS - Análise de Despesas",
    description="API para consulta de despesas de operadoras de planos de saúde",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "API ANS - Análise de Despesas",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "operadoras": "/api/operadoras",
            "operadora_detail": "/api/operadoras/{cnpj}",
            "despesas": "/api/operadoras/{cnpj}/despesas",
            "estatisticas": "/api/estatisticas"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
