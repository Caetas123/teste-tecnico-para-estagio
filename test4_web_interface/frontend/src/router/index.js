import { createRouter, createWebHistory } from 'vue-router'
import OperadorasList from '../components/OperadorasList.vue'
import OperadoraDetail from '../components/OperadoraDetail.vue'
import Dashboard from '../components/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: OperadorasList
  },
  {
    path: '/operadora/:cnpj',
    name: 'OperadoraDetail',
    component: OperadoraDetail
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
