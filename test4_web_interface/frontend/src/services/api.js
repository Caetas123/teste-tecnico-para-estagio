import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('Tempo de resposta excedido. Tente novamente.'))
    }
    
    if (!error.response) {
      return Promise.reject(new Error('Erro de conexão. Verifique sua internet.'))
    }
    
    const status = error.response.status
    if (status === 404) {
      return Promise.reject(new Error('Recurso não encontrado'))
    } else if (status === 500) {
      return Promise.reject(new Error('Erro no servidor. Tente novamente mais tarde.'))
    }
    
    return Promise.reject(error)
  }
)

export const operadorasService = {
  async getOperadoras(page = 1, limit = 10, busca = '') {
    const params = { page, limit }
    if (busca) params.busca = busca
    const response = await api.get('/api/operadoras', { params })
    return response.data
  },
  
  async getOperadoraByCnpj(cnpj) {
    const response = await api.get(`/api/operadoras/${cnpj}`)
    return response.data
  },
  
  async getDespesasOperadora(cnpj) {
    const response = await api.get(`/api/operadoras/${cnpj}/despesas`)
    return response.data
  },
  
  async getEstatisticas() {
    const response = await api.get('/api/estatisticas')
    return response.data
  }
}

export default api
