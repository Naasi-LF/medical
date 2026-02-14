import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConvId = ref(null)
  const messages = ref([])
  const loading = ref(false)

  async function fetchConversations() {
    const { data } = await api.get('/chat/conversations')
    conversations.value = data
  }

  async function createConversation() {
    const { data } = await api.post('/chat/conversations')
    conversations.value.unshift({ id: data.id, title: data.title, updated_at: '' })
    currentConvId.value = data.id
    messages.value = []
    return data.id
  }

  async function deleteConversation(convId) {
    await api.delete(`/chat/conversations/${convId}`)
    conversations.value = conversations.value.filter((c) => c.id !== convId)
    if (currentConvId.value === convId) {
      currentConvId.value = null
      messages.value = []
    }
  }

  async function loadMessages(convId) {
    currentConvId.value = convId
    const { data } = await api.get(`/chat/conversations/${convId}/messages`)
    messages.value = data
  }

  function selectConversation(convId) {
    if (convId === currentConvId.value) return
    loadMessages(convId)
  }

  return {
    conversations,
    currentConvId,
    messages,
    loading,
    fetchConversations,
    createConversation,
    deleteConversation,
    loadMessages,
    selectConversation,
  }
})
