<template>
  <div class="dashboard">
    <h2>Dashboard - Estatísticas Gerais</h2>

    <div v-if="store.loading" class="loading">Carregando estatísticas...</div>

    <div v-else-if="store.error" class="error-message">{{ store.error }}</div>

    <div v-else-if="store.estatisticas" class="stats-container">
      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-label">Total de Operadoras</div>
          <div class="stat-value">{{ store.estatisticas.total_operadoras }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Total de Despesas</div>
          <div class="stat-value">{{ formatCurrency(store.estatisticas.total_despesas) }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Média de Despesas</div>
          <div class="stat-value">{{ formatCurrency(store.estatisticas.media_despesas) }}</div>
        </div>
      </div>

      <div class="charts-container">
        <div class="chart-card">
          <h3>Top 5 Operadoras por Despesas</h3>
          <Bar v-if="chartDataTop5" :data="chartDataTop5" :options="chartOptions" />
        </div>

        <div class="chart-card">
          <h3>Distribuição de Despesas por UF</h3>
          <Pie v-if="chartDataUF" :data="chartDataUF" :options="pieOptions" />
        </div>
      </div>

      <div class="top-operadoras">
        <h3>Top 5 Operadoras</h3>
        <table class="top-table">
          <thead>
            <tr>
              <th>Posição</th>
              <th>Razão Social</th>
              <th>UF</th>
              <th>Total Despesas</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(op, index) in store.estatisticas.top_5_operadoras" :key="op.cnpj">
              <td>{{ index + 1 }}º</td>
              <td>{{ op.razao_social }}</td>
              <td>{{ op.uf || '-' }}</td>
              <td>{{ formatCurrency(op.total_despesas) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { Bar, Pie } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js'
import { useOperadorasStore } from '../stores/operadoras'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement)

const store = useOperadorasStore()

const chartDataTop5 = computed(() => {
  if (!store.estatisticas?.top_5_operadoras) return null
  
  return {
    labels: store.estatisticas.top_5_operadoras.map(op => op.razao_social.substring(0, 30)),
    datasets: [{
      label: 'Despesas Totais (R$)',
      data: store.estatisticas.top_5_operadoras.map(op => op.total_despesas),
      backgroundColor: '#4CAF50'
    }]
  }
})

const chartDataUF = computed(() => {
  if (!store.estatisticas?.distribuicao_uf) return null
  
  const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384']
  
  return {
    labels: store.estatisticas.distribuicao_uf.map(item => item.uf),
    datasets: [{
      label: 'Despesas por UF',
      data: store.estatisticas.distribuicao_uf.map(item => item.total_despesas),
      backgroundColor: colors
    }]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  }
}

const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right'
    }
  }
}

const formatCurrency = (value) => {
  if (!value) return 'R$ 0,00'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

onMounted(() => {
  store.fetchEstatisticas()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard h2 {
  color: #333;
  margin-bottom: 20px;
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

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
}

.stat-value {
  color: #333;
  font-size: 28px;
  font-weight: bold;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: 400px;
}

.chart-card h3 {
  color: #333;
  margin-bottom: 15px;
}

.top-operadoras {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.top-operadoras h3 {
  color: #333;
  margin-bottom: 15px;
}

.top-table {
  width: 100%;
  border-collapse: collapse;
}

.top-table thead {
  background: #f5f5f5;
}

.top-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
}

.top-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.top-table tbody tr:hover {
  background: #f9f9f9;
}
</style>
