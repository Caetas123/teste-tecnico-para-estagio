<template>
  <div class="operadoras-list">
    <div class="header">
      <h2>Operadoras de Planos de Saúde</h2>
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          @input="debouncedSearch"
          type="text" 
          placeholder="Buscar por razão social ou CNPJ..."
          class="search-input"
        />
      </div>
    </div>

    <div v-if="store.error" class="error-message">
      {{ store.error }}
      <button @click="retry" class="retry-btn">Tentar novamente</button>
    </div>

    <div v-if="store.loading" class="loading">
      Carregando...
    </div>

    <div v-else-if="store.operadoras.length === 0 && !store.error" class="empty-state">
      Nenhuma operadora encontrada
    </div>

    <div v-else class="table-container">
      <table class="operadoras-table">
        <thead>
          <tr>
            <th>CNPJ</th>
            <th>Razão Social</th>
            <th>UF</th>
            <th>Modalidade</th>
            <th>Total Despesas</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in store.operadoras" :key="op.id">
            <td>{{ formatCNPJ(op.cnpj) }}</td>
            <td>{{ op.razao_social }}</td>
            <td>{{ op.uf || '-' }}</td>
            <td>{{ op.modalidade || '-' }}</td>
            <td>{{ formatCurrency(op.total_despesas) }}</td>
            <td>
              <button @click="viewDetails(op.cnpj)" class="btn-details">
                Ver detalhes
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <button 
          @click="previousPage" 
          :disabled="store.pagination.page === 1"
          class="btn-pagination"
        >
          Anterior
        </button>
        
        <span class="pagination-info">
          Página {{ store.pagination.page }} de {{ store.pagination.total_pages }}
          ({{ store.pagination.total }} registros)
        </span>
        
        <button 
          @click="nextPage" 
          :disabled="store.pagination.page >= store.pagination.total_pages"
          class="btn-pagination"
        >
          Próxima
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOperadorasStore } from '../stores/operadoras'

const router = useRouter()
const store = useOperadorasStore()
const searchQuery = ref('')
let searchTimeout = null

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    store.fetchOperadoras(1, store.pagination.limit, searchQuery.value)
  }, 500)
}

const nextPage = () => {
  if (store.pagination.page < store.pagination.total_pages) {
    store.fetchOperadoras(store.pagination.page + 1, store.pagination.limit, searchQuery.value)
  }
}

const previousPage = () => {
  if (store.pagination.page > 1) {
    store.fetchOperadoras(store.pagination.page - 1, store.pagination.limit, searchQuery.value)
  }
}

const viewDetails = (cnpj) => {
  router.push(`/operadora/${cnpj}`)
}

const retry = () => {
  store.clearError()
  store.fetchOperadoras(store.pagination.page, store.pagination.limit, searchQuery.value)
}

const formatCNPJ = (cnpj) => {
  if (!cnpj) return ''
  return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
}

const formatCurrency = (value) => {
  if (!value) return 'R$ 0,00'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

onMounted(() => {
  store.fetchOperadoras()
})
</script>

<style scoped>
.operadoras-list {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  color: #333;
  margin-bottom: 15px;
}

.search-box {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  max-width: 500px;
  padding: 12px;
  font-size: 14px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.search-input:focus {
  outline: none;
  border-color: #4CAF50;
}

.error-message {
  padding: 15px;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.retry-btn {
  padding: 8px 16px;
  background: #c62828;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.operadoras-table {
  width: 100%;
  border-collapse: collapse;
}

.operadoras-table thead {
  background: #f5f5f5;
}

.operadoras-table th {
  padding: 15px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
}

.operadoras-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
}

.operadoras-table tbody tr:hover {
  background: #f9f9f9;
}

.btn-details {
  padding: 6px 12px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn-details:hover {
  background: #45a049;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f5f5f5;
}

.btn-pagination {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-pagination:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.pagination-info {
  color: #666;
  font-size: 14px;
}
</style>
