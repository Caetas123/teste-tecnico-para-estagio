<template>
  <div class="operadora-details">
    <button @click="goBack" class="btn-back">← Voltar</button>

    <div v-if="store.loading" class="loading">Carregando...</div>

    <div v-else-if="store.error" class="error-message">
      {{ store.error }}
    </div>

    <div v-else-if="store.currentOperadora" class="details-container">
      <div class="operadora-info">
        <h2>{{ store.currentOperadora.razao_social }}</h2>
        
        <div class="info-grid">
          <div class="info-item">
            <label>CNPJ:</label>
            <span>{{ formatCNPJ(store.currentOperadora.cnpj) }}</span>
          </div>
          
          <div class="info-item">
            <label>Registro ANS:</label>
            <span>{{ store.currentOperadora.registro_ans || '-' }}</span>
          </div>
          
          <div class="info-item">
            <label>Modalidade:</label>
            <span>{{ store.currentOperadora.modalidade || '-' }}</span>
          </div>
          
          <div class="info-item">
            <label>UF:</label>
            <span>{{ store.currentOperadora.uf || '-' }}</span>
          </div>
          
          <div class="info-item highlight">
            <label>Total de Despesas:</label>
            <span>{{ formatCurrency(store.currentOperadora.total_despesas) }}</span>
          </div>
          
          <div class="info-item">
            <label>Média por Trimestre:</label>
            <span>{{ formatCurrency(store.currentOperadora.media_por_trimestre) }}</span>
          </div>
          
          <div class="info-item">
            <label>Desvio Padrão:</label>
            <span>{{ formatCurrency(store.currentOperadora.desvio_padrao) }}</span>
          </div>
          
          <div class="info-item">
            <label>Número de Trimestres:</label>
            <span>{{ store.currentOperadora.numero_trimestres }}</span>
          </div>
        </div>
      </div>

      <div class="despesas-section">
        <h3>Histórico de Despesas</h3>
        
        <div v-if="store.despesasOperadora.length === 0" class="empty-state">
          Nenhuma despesa registrada
        </div>
        
        <div v-else>
          <table class="despesas-table">
            <thead>
              <tr>
                <th>Período</th>
                <th>Ano</th>
                <th>Trimestre</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="despesa in store.despesasOperadora" :key="despesa.id">
                <td>{{ despesa.periodo }}</td>
                <td>{{ despesa.ano }}</td>
                <td>{{ despesa.trimestre }}º Trimestre</td>
                <td>{{ formatCurrency(despesa.valor_despesas) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useOperadorasStore } from '../stores/operadoras'

const route = useRoute()
const router = useRouter()
const store = useOperadorasStore()

const goBack = () => {
  router.push('/')
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

onMounted(async () => {
  const cnpj = route.params.cnpj
  await store.fetchOperadoraByCnpj(cnpj)
  await store.fetchDespesasOperadora(cnpj)
})
</script>

<style scoped>
.operadora-details {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.btn-back {
  padding: 10px 20px;
  background: #666;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 20px;
}

.btn-back:hover {
  background: #555;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  padding: 15px;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
}

.details-container {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.operadora-info h2 {
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #4CAF50;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.info-item {
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
}

.info-item.highlight {
  background: #e8f5e9;
  border: 2px solid #4CAF50;
}

.info-item label {
  display: block;
  font-weight: 600;
  color: #666;
  font-size: 12px;
  margin-bottom: 5px;
  text-transform: uppercase;
}

.info-item span {
  display: block;
  font-size: 16px;
  color: #333;
}

.despesas-section {
  margin-top: 30px;
}

.despesas-section h3 {
  color: #333;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
  background: #f5f5f5;
  border-radius: 4px;
}

.despesas-table {
  width: 100%;
  border-collapse: collapse;
}

.despesas-table thead {
  background: #f5f5f5;
}

.despesas-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
}

.despesas-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.despesas-table tbody tr:hover {
  background: #f9f9f9;
}
</style>
