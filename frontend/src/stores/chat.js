import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConvId = ref(null)
  const messages = ref([])
  const loading = ref(false)

  let _loadId = 0

  async function fetchConversations() {
    try {
      const { data } = await api.get('/chat/conversations')
      conversations.value = data
    } catch (e) {
      console.error('fetchConversations failed', e)
    }
  }

  async function createConversation() {
    try {
      const { data } = await api.post('/chat/conversations')
      conversations.value.unshift({ id: data.id, title: data.title, updated_at: '' })
      currentConvId.value = data.id
      messages.value = []
      return data.id
    } catch (e) {
      console.error('createConversation failed', e)
    }
  }

  async function deleteConversation(convId) {
    try {
      await api.delete(`/chat/conversations/${convId}`)
      conversations.value = conversations.value.filter((c) => c.id !== convId)
      if (currentConvId.value === convId) {
        currentConvId.value = null
        messages.value = []
      }
    } catch (e) {
      console.error('deleteConversation failed', e)
    }
  }

  async function loadMessages(convId) {
    const id = ++_loadId
    currentConvId.value = convId
    try {
      const { data } = await api.get(`/chat/conversations/${convId}/messages`)
      if (_loadId === id) {
        messages.value = data
      }
    } catch (e) {
      console.error('loadMessages failed', e)
    }
  }

  function selectConversation(convId) {
    if (convId === currentConvId.value) return
    loadMessages(convId)
  }

  async function renameConversation(convId, newTitle) {
    try {
      await api.patch(`/chat/conversations/${convId}`, { title: newTitle })
      const conv = conversations.value.find((c) => c.id === convId)
      if (conv) conv.title = newTitle
    } catch (e) {
      console.error('renameConversation failed', e)
    }
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
    renameConversation,
  }
})
