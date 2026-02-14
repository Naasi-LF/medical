<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path d="M8 16c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8" stroke="#4f6ef7" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="16" cy="16" r="3" fill="#4f6ef7"/>
          </svg>
        </div>
        <h1>胃病智能问答</h1>
      </div>

      <div class="tabs">
        <button :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="field">
          <input v-model="username" type="text" placeholder="用户名" autocomplete="username" />
        </div>
        <div class="field">
          <input v-model="password" type="password" placeholder="密码" autocomplete="current-password" />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="submit-btn" :disabled="submitting">
          {{ submitting ? '请稍候...' : (mode === 'login' ? '登录' : '注册') }}
        </button>
      </form>

      <p class="footer-hint">基于 RAG + 知识图谱的个性化医学问答</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const mode = ref('login')
const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleSubmit() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }
  submitting.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(username.value, password.value)
    } else {
      await auth.register(username.value, password.value)
    }
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || '操作失败，请重试'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f3f5;
}

.login-card {
  width: 380px;
  background: #fff;
  border-radius: 24px;
  padding: 44px 36px 36px;
  box-shadow: 0 2px 24px rgba(0, 0, 0, 0.06);
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: #f0f3ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-area h1 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  letter-spacing: 0.5px;
}

.tabs {
  display: flex;
  margin-bottom: 24px;
  background: #f5f6f8;
  border-radius: 12px;
  padding: 3px;
}

.tabs button {
  flex: 1;
  padding: 9px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #999;
  transition: all 0.2s;
}

.tabs button.active {
  background: #fff;
  color: #1a1a2e;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.field {
  margin-bottom: 14px;
}

.field input {
  width: 100%;
  padding: 12px 16px;
  border: 1.5px solid #ecedf0;
  border-radius: 12px;
  font-size: 14px;
  color: #1a1a2e;
  background: #fafbfc;
  transition: all 0.2s;
}

.field input::placeholder { color: #bbb; }

.field input:focus {
  border-color: #4f6ef7;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(79, 110, 247, 0.08);
}

.error {
  color: #e74c3c;
  font-size: 13px;
  margin-bottom: 12px;
  text-align: center;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #4f6ef7;
  color: #fff;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.2s;
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) { background: #3d5bd9; }
.submit-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.footer-hint {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 24px;
}
</style>
