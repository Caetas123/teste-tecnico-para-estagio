import { defineStore } from 'pinia'
import { operadorasService } from '../services/api'

export const useOperadorasStore = defineStore('operadoras', {
  state: () => ({
    operadoras: [],
    currentOperadora: null,
    despesasOperadora: [],
    estatisticas: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      limit: 10,
      total: 0,
      total_pages: 0
    },
    busca: '',
    cache: new Map()
  }),
  
  actions: {
    async fetchOperadoras(page = 1, limit = 10, busca = '') {
      this.loading = true
      this.error = null
      
      try {
        const data = await operadorasService.getOperadoras(page, limit, busca)
        this.operadoras = data.data
        this.pagination = {
          page: data.page,
          limit: data.limit,
          total: data.total,
          total_pages: data.total_pages
        }
        this.busca = busca
      } catch (error) {
        this.error = error.message
        this.operadoras = []
      } finally {
        this.loading = false
      }
    },
    
    async fetchOperadoraByCnpj(cnpj) {
      this.loading = true
      this.error = null
      
      const cached = this.cache.get(`operadora_${cnpj}`)
      if (cached && Date.now() - cached.timestamp < 300000) {
        this.currentOperadora = cached.data
        this.loading = false
        return
      }
      
      try {
        const data = await operadorasService.getOperadoraByCnpj(cnpj)
        this.currentOperadora = data
        this.cache.set(`operadora_${cnpj}`, { data, timestamp: Date.now() })
      } catch (error) {
        this.error = error.message
        this.currentOperadora = null
      } finally {
        this.loading = false
      }
    },
    
    async fetchDespesasOperadora(cnpj) {
      this.loading = true
      this.error = null
      
      try {
        const data = await operadorasService.getDespesasOperadora(cnpj)
        this.despesasOperadora = data.despesas
      } catch (error) {
        this.error = error.message
        this.despesasOperadora = []
      } finally {
        this.loading = false
      }
    },
    
    async fetchEstatisticas() {
      if (this.estatisticas) {
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        const data = await operadorasService.getEstatisticas()
        this.estatisticas = data
      } catch (error) {
        this.error = error.message
        this.estatisticas = null
      } finally {
        this.loading = false
      }
    },
    
    clearError() {
      this.error = null
    }
  }
})
