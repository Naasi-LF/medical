<template>
  <div class="chat-layout">
    <!-- Sidebar -->
    <ChatSidebar />

    <!-- Main area -->
    <div class="main-area">
      <!-- Header -->
      <header class="topbar">
        <div class="topbar-left">
          <button class="icon-btn" @click="toggleSidebar" title="切换侧栏">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
          <span class="topbar-title">{{ currentTitle }}</span>
        </div>
        <div class="topbar-right">
          <button class="icon-btn" @click="showMemory = !showMemory" :class="{ active: showMemory }" title="个人健康档案">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="7.5" stroke="currentColor" stroke-width="1.5"/><circle cx="9" cy="7" r="2" fill="currentColor"/><path d="M5 14c0-2.2 1.8-4 4-4s4 1.8 4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
          <span class="username">{{ auth.username }}</span>
          <button class="icon-btn" @click="handleLogout" title="退出登录">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M6.75 15.75H3.75a1.5 1.5 0 01-1.5-1.5v-10.5a1.5 1.5 0 011.5-1.5h3M12 12.75L15.75 9 12 5.25M7.5 9h8.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
      </header>

      <!-- Messages -->
      <div class="messages-area" ref="messagesRef">
        <div v-if="!chat.currentConvId && chat.messages.length === 0" class="welcome">
          <div class="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <rect width="48" height="48" rx="16" fill="#eef1fe"/>
              <path d="M16 24c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8" stroke="#4f6ef7" stroke-width="2.5" stroke-linecap="round"/>
              <circle cx="24" cy="24" r="3" fill="#4f6ef7"/>
            </svg>
          </div>
          <h2>你好，有什么可以帮助你的？</h2>
          <p>我是胃病智能问答助手，可以回答关于胃炎、胃溃疡等问题</p>
          <div class="suggestions">
            <button @click="askQuestion('肠胃炎应该吃什么药？')">肠胃炎应该吃什么药？</button>
            <button @click="askQuestion('晚上反酸怎么缓解？')">晚上反酸怎么缓解？</button>
            <button @click="askQuestion('胃炎和胃溃疡区别是什么？')">胃炎和胃溃疡区别是什么？</button>
          </div>
        </div>

        <template v-for="(msg, idx) in chat.messages" :key="idx">
          <ChatMessage :message="msg" />
        </template>

        <!-- Streaming message -->
        <ChatMessage v-if="streamingMsg" :message="streamingMsg" :streaming="true" />
      </div>

      <!-- Composer -->
      <div class="composer">
        <div class="composer-inner">
          <div class="composer-box">
            <textarea
              ref="textareaRef"
              v-model="question"
              placeholder="给胃病助手发送消息"
              rows="1"
              @input="autoResize"
              @keydown.enter.ctrl.exact.prevent="sendMessage"
              @keydown.enter.meta.exact.prevent="sendMessage"
            ></textarea>
            <div class="composer-bottom">
              <div class="pill-toggles">
                <button class="pill" :class="{ active: thinkMode }" @click="thinkMode = !thinkMode">
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.2"/><path d="M5.5 7h3M7 5.5v3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                  <span>深度思考</span>
                </button>
              </div>
              <button class="send-circle" @click="sendMessage" :disabled="!question.trim() || sending">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 14V4M5 7.5L9 4l4 3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Memory panel -->
    <MemoryPanel v-if="showMemory" @close="showMemory = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import ChatSidebar from '../components/ChatSidebar.vue'
import ChatMessage from '../components/ChatMessage.vue'
import MemoryPanel from '../components/MemoryPanel.vue'

const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()

const question = ref('')
const thinkMode = ref(true)
const sending = ref(false)
const showMemory = ref(false)
const streamingMsg = ref(null)
const messagesRef = ref(null)
const textareaRef = ref(null)

const currentTitle = computed(() => {
  if (!chat.currentConvId) return '新对话'
  const conv = chat.conversations.find((c) => c.id === chat.currentConvId)
  return conv?.title || '对话'
})

onMounted(() => {
  chat.fetchConversations()
})

function toggleSidebar() {
  document.querySelector('.chat-layout')?.classList.toggle('sidebar-collapsed')
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    const el = messagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function askQuestion(q) {
  question.value = q
  sendMessage()
}

async function sendMessage() {
  const q = question.value.trim()
  if (!q || sending.value) return

  sending.value = true
  question.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }

  chat.messages.push({ role: 'user', content: q })
  scrollToBottom()

  streamingMsg.value = {
    role: 'assistant',
    content: '',
    thinking: '',
    sources: [],
    references: [],
  }

  try {
    const token = auth.token
    const body = {
      question: q,
      conversation_id: chat.currentConvId || null,
      think_mode: thinkMode.value,
      top_k: 8,
    }

    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n')
      buffer = parts.pop() || ''

      for (const line of parts) {
        const clean = line.trim()
        if (!clean) continue
        try {
          const evt = JSON.parse(clean)

          if (evt.event === 'reasoning') {
            streamingMsg.value.thinking += evt.data
          } else if (evt.event === 'answer') {
            streamingMsg.value.content += evt.data
          } else if (evt.event === 'references') {
            streamingMsg.value.references = evt.data || []
          } else if (evt.event === 'sources') {
            streamingMsg.value.sources = evt.data || []
          } else if (evt.event === 'answer_final') {
            streamingMsg.value.content = evt.data
          } else if (evt.event === 'conversation_id') {
            if (!chat.currentConvId) {
              chat.currentConvId = evt.data
              chat.fetchConversations()
            }
          } else if (evt.event === 'error') {
            streamingMsg.value.content += `\n[错误] ${evt.data}`
          }
        } catch {
          // skip malformed
        }
      }
      scrollToBottom()
    }

    chat.messages.push({ ...streamingMsg.value })
  } catch (err) {
    if (streamingMsg.value) {
      streamingMsg.value.content += `\n[错误] ${err.message}`
    }
    chat.messages.push({ ...streamingMsg.value })
  } finally {
    streamingMsg.value = null
    sending.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f2f3f5;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-size: 13px;
  color: #999;
}

.icon-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #999;
  transition: all 0.15s;
}

.icon-btn:hover { background: #f5f5f5; color: #555; }
.icon-btn.active { background: #eef1fe; color: #4f6ef7; }

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 0 24px;
}

.welcome-icon { margin-bottom: 20px; }

.welcome h2 {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1a1a2e;
}

.welcome p {
  color: #aaa;
  font-size: 14px;
  margin-bottom: 32px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.suggestions button {
  padding: 10px 20px;
  border: 1px solid #e8e8e8;
  border-radius: 24px;
  font-size: 13px;
  color: #555;
  transition: all 0.2s;
  background: #fff;
}

.suggestions button:hover {
  border-color: #4f6ef7;
  color: #4f6ef7;
  background: #f5f7ff;
}

/* ── Composer (DeepSeek style) ── */
.composer {
  padding: 0 16px 24px;
  flex-shrink: 0;
}

.composer-inner {
  max-width: 768px;
  margin: 0 auto;
}

.composer-box {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 20px;
  padding: 14px 16px 10px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s;
}

.composer-box:focus-within {
  border-color: #d0d5e0;
}

.composer-box textarea {
  width: 100%;
  border: none;
  resize: none;
  line-height: 1.5;
  font-size: 14px;
  max-height: 140px;
  overflow-y: auto;
  color: #1a1a2e;
  background: transparent;
}

.composer-box textarea::placeholder { color: #bbb; }

.composer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.pill-toggles {
  display: flex;
  gap: 8px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid #e0e0e0;
  color: #888;
  background: #fff;
  transition: all 0.2s;
}

.pill:hover {
  border-color: #ccc;
  color: #666;
}

.pill.active {
  background: #4f6ef7;
  color: #fff;
  border-color: #4f6ef7;
}

.send-circle {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #4f6ef7;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.send-circle:hover:not(:disabled) { background: #3d5bd9; }
.send-circle:disabled { opacity: 0.35; cursor: not-allowed; }

.chat-layout.sidebar-collapsed :deep(.sidebar) { display: none; }

@media (max-width: 768px) {
  :deep(.sidebar) { display: none; }
  .chat-layout.sidebar-collapsed :deep(.sidebar) { display: flex; }
}
</style>
