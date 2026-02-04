# TESTE 4 - API E INTERFACE WEB

## Visão Geral
Interface web completa desenvolvida com Vue.js 3 e FastAPI para consulta e análise de dados das operadoras de planos de saúde.

## Arquitetura

```
test4_web_interface/
├── backend/              # API REST (FastAPI)
│   ├── app.py           # Aplicação principal
│   ├── routes.py        # Definição de rotas
│   ├── models.py        # Modelos Pydantic
│   ├── database.py      # Conexão com BD/CSVs
│   ├── postman_collection.json
│   └── test_search.py   # Testes unitários
│
└── frontend/            # Interface Vue.js 3
    ├── src/
    │   ├── App.vue      # Componente raiz
    │   ├── main.js      # Entry point
    │   ├── components/  # Componentes Vue
    │   │   ├── Dashboard.vue
    │   │   ├── OperadorasList.vue
    │   │   └── OperadoraDetail.vue
    │   ├── router/      # Vue Router
    │   │   └── index.js
    │   ├── services/    # API client
    │   │   └── api.js
    │   └── stores/      # Pinia stores
    │       └── operadoras.js
    ├── package.json
    └── vite.config.js
```

## Como Executar

### Backend (FastAPI)

```powershell
cd test4_web_interface\backend
python app.py
```

**Servidor**: http://localhost:8000  
**Documentação Swagger**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

### Frontend (Vue.js)

```bash
cd test4_web_interface/frontend
npm install
npm run dev
```

**Interface**: http://localhost:5173

## API - Rotas Disponíveis

### GET /api/operadoras
Lista todas as operadoras com paginação.

**Parâmetros**:
- `page` (int, default=1): Número da página
- `limit` (int, default=20): Registros por página
- `search` (str, optional): Busca por razão social ou CNPJ

**Resposta**:
```json
{
  "data": [
    {
      "cnpj": "12345678000199",
      "razao_social": "Operadora Exemplo S.A.",
      "uf": "SP",
      "modalidade": "Medicina de Grupo",
      "registro_ans": "123456"
    }
  ],
  "total": 1250,
  "page": 1,
  "limit": 20,
  "total_pages": 63
}
```

### GET /api/operadoras/{cnpj}
Retorna detalhes de uma operadora específica.

**Parâmetros**:
- `cnpj` (str): CNPJ da operadora (com ou sem formatação)

**Resposta**:
```json
{
  "cnpj": "12345678000199",
  "razao_social": "Operadora Exemplo S.A.",
  "uf": "SP",
  "modalidade": "Medicina de Grupo",
  "registro_ans": "123456",
  "total_despesas": 15000000.50,
  "numero_trimestres": 3
}
```

### GET /api/operadoras/{cnpj}/despesas
Retorna histórico de despesas da operadora.

**Resposta**:
```json
{
  "cnpj": "12345678000199",
  "razao_social": "Operadora Exemplo S.A.",
  "despesas": [
    {
      "ano": 2024,
      "trimestre": 1,
      "valor": 4800000.00,
      "periodo": "2024-Q1"
    },
    {
      "ano": 2024,
      "trimestre": 2,
      "valor": 5100000.25,
      "periodo": "2024-Q2"
    }
  ],
  "total": 15000000.50
}
```

### GET /api/estatisticas
Retorna estatísticas agregadas do sistema.

**Resposta**:
```json
{
  "total_operadoras": 1250,
  "total_despesas": 25000000000.00,
  "media_despesas": 20000000.00,
  "top_5_operadoras": [
    {
      "razao_social": "Maior Operadora S.A.",
      "total_despesas": 500000000.00,
      "uf": "SP"
    }
  ],
  "distribuicao_uf": [
    {
      "uf": "SP",
      "total": 10000000000.00,
      "percentual": 40.0
    }
  ]
}
```

## Decisões Técnicas - Backend

### 1. Escolha do Framework: FastAPI

**Decisão**: FastAPI (ao invés de Flask)

**Justificativa**:

| Critério | FastAPI | Flask | Escolhido |
|----------|---------|-------|-----------|
| **Performance** | (async nativo) | (sync) |  FastAPI |
| **Documentação auto** |  Swagger/ReDoc |  Manual |  FastAPI |
| **Validação de dados** |  Pydantic | Manual |  FastAPI |
| **Type hints** |  Nativo |  Opcional |  FastAPI |
| **Curva de aprendizado** | Moderada | Fácil |  FastAPI |
| **Ecossistema** | Moderno | Maduro | - |

**Vantagens do FastAPI**:
```python
# Validação automática com Pydantic
class OperadoraResponse(BaseModel):
    cnpj: str
    razao_social: str
    uf: str = "N/A"

@app.get("/api/operadoras/{cnpj}", response_model=OperadoraResponse)
async def get_operadora(cnpj: str):
    # Validação automática de entrada/saída
    # Documentação auto-gerada
    # Type safety
```

**Alternativa (Flask)**:
```python
# Validação manual
@app.route('/api/operadoras/<cnpj>')
def get_operadora(cnpj):
    if not cnpj or len(cnpj) != 14:
        return {"error": "CNPJ inválido"}, 400
    # ... validação manual
```

**Conclusão**: FastAPI escolhido por produtividade e recursos modernos.

### 2. Estratégia de Paginação: Offset-based

**Decisão**: Paginação **offset-based** (LIMIT/OFFSET)

**Implementação**:
```python
@app.get("/api/operadoras")
async def list_operadoras(page: int = 1, limit: int = 20):
    offset = (page - 1) * limit
    data = get_data(limit=limit, offset=offset)
    total = count_total()
    
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": (total + limit - 1) // limit
    }
```

**Comparação**:

| Estratégia | Implementação | Performance | Casos de uso | Escolhida |
|------------|---------------|-------------|--------------|-----------|
| **Offset-based** | `LIMIT 20 OFFSET 40` | (lenta em grandes offsets) | Tabelas estáveis | Sim |
| **Cursor-based** | `WHERE id > last_id LIMIT 20` |  (sempre rápida) | Feeds infinitos | Não |
| **Keyset pagination** | `WHERE (ano, id) > (2024, 100)` | | Grandes volumes | Não |

 **Offset-based escolhido por**:
- Simples de implementar e entender
- Permite navegação direta para qualquer página
- Adequado para volumes moderados (<100k registros)
- Frontend pode mostrar "Página X de Y"
- Usuários esperan esse comportamento

 **Cursor-based descartado**:
- Não permite pular páginas (somente next/previous)
- Mais complexo para UI/UX tradicional
- Melhor para scroll infinito (não é o caso)

 **Keyset pagination descartado**:
- Complexidade desnecessária para o volume de dados
- Requer índices compostos específicos
- Dificulta ordenação dinâmica

**Performance esperada**:
```
Volume: 1.000 - 5.000 operadoras
Página 1 (OFFSET 0):    ~10ms
Página 50 (OFFSET 1000): ~15ms
Página 100 (OFFSET 2000): ~20ms
```

### 3. Cache vs Queries Diretas para /api/estatisticas

**Decisão**: **Cache em memória com TTL de 5 minutos** (Opção B)

**Implementação**:
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache global com timestamp
_stats_cache = {"data": None, "timestamp": None}
CACHE_TTL = timedelta(minutes=5)

@app.get("/api/estatisticas")
async def get_estatisticas():
    now = datetime.now()
    
    # Verifica se cache é válido
    if _stats_cache["data"] and _stats_cache["timestamp"]:
        if now - _stats_cache["timestamp"] < CACHE_TTL:
            return _stats_cache["data"]
    
    # Calcula estatísticas
    stats = calcular_estatisticas()
    
    # Atualiza cache
    _stats_cache["data"] = stats
    _stats_cache["timestamp"] = now
    
    return stats
```

**Comparação**:

| Estratégia | Latência | Carga BD | Consistência | Complexidade | Escolhida |
|------------|----------|----------|--------------|--------------|-----------|
| **Sempre calcular** | Alta (500ms) | Alta | Tempo real | Baixa | Não |
| **Cache 5min** | Baixa (<10ms) | Baixa | 5min atraso | Moderada | Sim |
| **Tabela pré-calc** | Baixa | Muito baixa | Batch update | Alta | Não |

 **Cache escolhido por**:
- Dados de estatísticas mudam raramente (trimestral)
- Dashboard é acessado frequentemente
- Reduz carga no BD/CSV em 99%
- Latência consistente (<10ms)
- Implementação simples

**Análise de impacto**:
```
Sem cache:
  100 usuários/hora → 100 queries pesadas → ~500ms cada
  Carga total: 50 segundos de processamento

Com cache (5min):
  100 usuários/hora → ~12 queries (5min TTL) → resto do cache
  Carga total: 6 segundos de processamento
  Redução: 88%
```

**Trade-off aceito**:
-  Dados podem ter até 5min de atraso
-  Aceitável pois dados são atualizados trimestralmente

**Invalidação manual** (se necessário):
```python
@app.post("/api/estatisticas/refresh")
async def refresh_stats():
    _stats_cache["data"] = None
    return {"message": "Cache invalidado"}
```

### 4. Estrutura de Resposta da API

**Decisão**: Dados + metadados (Opção B)

**Formato padrão**:
```json
{
  "data": [...],
  "total": 1250,
  "page": 1,
  "limit": 20,
  "total_pages": 63
}
```

**Comparação**:

| Formato | Frontend | Info extra | Tamanho | Escolhido |
|---------|----------|------------|---------|-----------|
| **Apenas dados** `[{...}]` | Simples | Sem metadados | Pequeno | Não |
| **Dados + meta** `{data, total, page}` | Rico | Paginação completa | Moderado | Sim |

**Justificativa**:

**Dados + metadados escolhido por**:
- Frontend precisa de `total` para calcular páginas
- `page` e `limit` confirmam os parâmetros
- Facilita implementação de paginação no UI
- Padrão da indústria (REST API best practices)

**Uso no frontend**:
```javascript
async function loadOperadoras(page = 1) {
  const response = await api.get(`/operadoras?page=${page}&limit=20`);
  
  // Metadados disponíveis
  console.log(`Página ${response.page} de ${response.total_pages}`);
  console.log(`Total de registros: ${response.total}`);
  
  // Dados
  this.operadoras = response.data;
}
```

## Decisões Técnicas - Frontend

### 1. Estratégia de Busca/Filtro: Híbrida

**Decisão**: **Busca no servidor + filtro local** (Opção C)

**Implementação**:
```javascript
// services/api.js
export async function searchOperadoras(query, page = 1) {
  // Busca no servidor para grandes datasets
  return axios.get(`/api/operadoras?search=${query}&page=${page}`);
}

// components/OperadorasList.vue
async function buscar() {
  if (searchTerm.length >= 3) {
    // Busca no servidor (>= 3 caracteres)
    const result = await api.searchOperadoras(searchTerm);
    operadoras.value = result.data;
  } else if (searchTerm.length > 0) {
    // Filtro local (1-2 caracteres)
    operadoras.value = todasOperadoras.filter(op => 
      op.razao_social.toLowerCase().includes(searchTerm.toLowerCase())
    );
  } else {
    // Sem filtro
    operadoras.value = todasOperadoras;
  }
}
```

**Comparação**:

| Estratégia | Performance | UX | Tráfego rede | Escolhida |
|------------|-------------|----|--------------|- ---------|
| **Servidor** | Alta (grandes volumes) | Moderada (delay de rede) | Alto | Não |
| **Cliente** | Baixa (lento >1000 itens) | Alta (instantâneo) | Baixo | Não |
| **Híbrido** | Alta | Alta | Moderado | Sim |

**Justificativa**:

**Híbrido escolhido por**:
- Busca curta (1-2 chars): Filtro local instantâneo
- Busca longa (3+ chars): Busca no servidor com precisão
- Melhor experiência do usuário
- Balanceia performance e tráfego

**Debounce implementado**:
```javascript
import { debounce } from 'lodash-es';

const buscarDebounced = debounce(async () => {
  await buscar();
}, 300); // 300ms de espera
```

### 2. Gerenciamento de Estado: Pinia

**Decisão**: **Pinia** (Opção B)

**Implementação**:
```javascript
// stores/operadoras.js
import { defineStore } from 'pinia';

export const useOperadorasStore = defineStore('operadoras', {
  state: () => ({
    operadoras: [],
    currentOperadora: null,
    loading: false,
    error: null
  }),
  
  actions: {
    async fetchOperadoras(page = 1) {
      this.loading = true;
      try {
        const response = await api.getOperadoras(page);
        this.operadoras = response.data;
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
});
```

**Comparação**:

| Abordagem | Complexidade | Devtools | TypeScript | Composição | Escolhida |
|-----------|--------------|----------|------------|------------|-----------|
| **Props/Events** | Baixa | Não | Manual | Não | Não |
| **Pinia** | Moderada | Sim | Sim | Sim | Sim |
| **Composables** | Baixa-Moderada | Limitado | Sim | Sim | Não |

**Justificativa**:

**Pinia escolhido por**:
- Estado centralizado e reativo
- Suporte a DevTools para debugging
- TypeScript nativo
- API mais simples que Vuex
- Recomendação oficial do Vue 3

**Uso em componentes**:
```vue
<script setup>
import { useOperadorasStore } from '@/stores/operadoras';

const store = useOperadorasStore();

onMounted(() => {
  store.fetchOperadoras();
});
</script>

<template>
  <div v-if="store.loading">Carregando...</div>
  <div v-else-if="store.error">Erro: {{ store.error }}</div>
  <ul v-else>
    <li v-for="op in store.operadoras" :key="op.cnpj">
      {{ op.razao_social }}
    </li>
  </ul>
</template>
```

### 3. Performance da Tabela: Virtual scrolling

**Decisão**: Paginação tradicional (volumes moderados) + preparado para virtual scroll

**Implementação atual**:
```vue
<template>
  <table>
    <tbody>
      <tr v-for="operadora in paginatedData" :key="operadora.cnpj">
        <td>{{ operadora.razao_social }}</td>
        <td>{{ operadora.uf }}</td>
        <td>{{ formatCurrency(operadora.total_despesas) }}</td>
      </tr>
    </tbody>
  </table>
  
  <Pagination 
    :current-page="currentPage" 
    :total-pages="totalPages" 
    @change="changePage" 
  />
</template>
```

**Comparação**:

| Estratégia | Renderiza | Performance | UX | Volume suportado | Escolhida |
|------------|-----------|-------------|----|--------------------|-----------|
| **Renderizar tudo** | Todos os itens | Lento >500 | Simples | <500 | Não |
| **Paginação** | 20-50 por página | Rápido | Familiar | <100k | Sim |
| **Virtual scroll** | Apenas visíveis | Muito rápido | Menos familiar | Ilimitado | Aviso: futuro |

**Justificativa**:

**Paginação escolhida por**:
- Volume esperado: 1.000-5.000 operadoras
- UX familiar para usuários
- Implementação simples e confiável
- Performance adequada (20-50 itens/página)

**Preparado para virtual scroll** (se volume crescer):
```vue
<!-- Futuro: usar vue-virtual-scroller -->
<RecycleScroller
  :items="operadoras"
  :item-size="50"
  key-field="cnpj"
>
  <template #default="{ item }">
    <OperadoraRow :operadora="item" />
  </template>
</RecycleScroller>
```

### 4. Tratamento de Erros e Loading

**Abordagem**: Estados explícitos + mensagens contextuais

**Implementação**:
```vue
<script setup>
const loading = ref(false);
const error = ref(null);
const data = ref(null);

async function loadData() {
  loading.value = true;
  error.value = null;
  
  try {
    data.value = await api.getOperadoras();
  } catch (err) {
    // Mensagens específicas por tipo de erro
    if (err.response?.status === 404) {
      error.value = "Operadora não encontrada";
    } else if (err.response?.status === 500) {
      error.value = "Erro no servidor. Tente novamente mais tarde.";
    } else if (!navigator.onLine) {
      error.value = "Sem conexão com a internet";
    } else {
      error.value = "Erro ao carregar dados";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <!-- Loading state -->
  <div v-if="loading" class="loading-spinner">
    <Spinner />
    <p>Carregando dados...</p>
  </div>
  
  <!-- Error state -->
  <div v-else-if="error" class="error-message">
    <Icon name="alert" />
    <p>{{ error }}</p>
    <button @click="loadData">Tentar novamente</button>
  </div>
  
  <!-- Empty state -->
  <div v-else-if="!data || data.length === 0" class="empty-state">
    <Icon name="inbox" />
    <p>Nenhuma operadora encontrada</p>
  </div>
  
  <!-- Success state -->
  <div v-else>
    <OperadorasList :operadoras="data" />
  </div>
</template>
```

**Decisão**: **Mensagens específicas** (ao invés de genéricas)

**Justificativa**:
- Usuário entende o que aconteceu
- Pode tomar ação apropriada
- Melhor experiência de debugging
- Profissionalismo

**Estados tratados**:
1. **Loading**: Spinner + mensagem descritiva
2. **Erro de rede**: Mensagem de conexão
3. **Erro 404**: "Não encontrado"
4. **Erro 500**: "Erro no servidor"
5. **Dados vazios**: "Nenhum resultado"
6. **Sucesso**: Renderiza dados

## Gráficos - Chart.js

**Biblioteca**: Chart.js 4.x

**Gráfico implementado**: Distribuição de despesas por UF (Pizza)

```vue
<template>
  <canvas ref="chartCanvas"></canvas>
</template>

<script setup>
import { Chart } from 'chart.js/auto';

const chartCanvas = ref(null);

onMounted(async () => {
  const stats = await api.getEstatisticas();
  
  new Chart(chartCanvas.value, {
    type: 'pie',
    data: {
      labels: stats.distribuicao_uf.map(d => d.uf),
      datasets: [{
        data: stats.distribuicao_uf.map(d => d.total),
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', ...]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'right' },
        tooltip: {
          callbacks: {
            label: (context) => {
              const value = formatCurrency(context.parsed);
              const percent = context.parsed / total * 100;
              return `${context.label}: ${value} (${percent.toFixed(1)}%)`;
            }
          }
        }
      }
    }
  });
});
</script>
```

## Coleção Postman

**Arquivo**: `backend/postman_collection.json`

**Rotas documentadas**:
1. GET /api/operadoras (com paginação e busca)
2. GET /api/operadoras/{cnpj}
3. GET /api/operadoras/{cnpj}/despesas
4. GET /api/estatisticas

**Exemplos incluídos**:
- Requisições de sucesso
- Casos de erro (404, 400)
- Parâmetros opcionais

**Como importar**:
1. Abrir Postman
2. File → Import
3. Selecionar `postman_collection.json`
4. Executar requests

## Dependências

### Backend
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pandas>=2.0.0
pydantic>=2.0.0
python-multipart>=0.0.6
```

### Frontend
```json
{
  "dependencies": {
    "vue": "^3.3.8",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.2",
    "chart.js": "^4.4.0"
  }
}
```

## Execução Completa

```bash
# Terminal 1: Backend
cd test4_web_interface/backend
python app.py

# Terminal 2: Frontend
cd test4_web_interface/frontend
npm install
npm run dev

# Abrir navegador
http://localhost:5173
```

## Melhorias Futuras

1. **Autenticação**: JWT tokens para rotas protegidas
2. **Testes E2E**: Playwright/Cypress
3. **SSR**: Nuxt.js para SEO
4. **PWA**: Service workers para offline
5. **WebSockets**: Atualizações em tempo real
6. **Docker**: Containerização da aplicação
