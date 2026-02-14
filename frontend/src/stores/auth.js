import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(localStorage.getItem('userId') || '')
  const username = ref(localStorage.getItem('username') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function register(user, pass) {
    const { data } = await api.post('/auth/register', {
      username: user,
      password: pass,
    })
    _setAuth(data)
    return data
  }

  async function login(user, pass) {
    const { data } = await api.post('/auth/login', {
      username: user,
      password: pass,
    })
    _setAuth(data)
    return data
  }

  function logout() {
    token.value = ''
    userId.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('username')
  }

  function _setAuth(data) {
    token.value = data.access_token
    userId.value = data.user_id
    username.value = data.username
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userId', data.user_id)
    localStorage.setItem('username', data.username)
  }

  return { token, userId, username, isLoggedIn, register, login, logout }
})
