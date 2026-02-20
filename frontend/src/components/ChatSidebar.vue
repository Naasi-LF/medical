<template>
  <aside class="sidebar">
    <div class="sidebar-top">
      <button class="new-chat-btn" @click="newChat" aria-label="开启新对话">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.2"/><path d="M8 4v8M4 8h8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
        <span>开启新对话</span>
      </button>
    </div>

    <div class="conv-list">
      <div
        v-for="conv in chat.conversations"
        :key="conv.id"
        class="conv-item"
        :class="{ active: conv.id === chat.currentConvId }"
        @click="chat.selectConversation(conv.id)"
        @dblclick.stop="startRename(conv)"
      >
        <svg class="conv-icon" width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 3.5h10M2 7h7M2 10.5h5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
        <input
          v-if="editingId === conv.id"
          v-model="editTitle"
          class="rename-input"
          @blur="finishRename(conv.id)"
          @keydown.enter="finishRename(conv.id)"
          @keydown.escape="editingId = null"
          @click.stop
          ref="renameInputRef"
        />
        <span v-else class="conv-title">{{ conv.title }}</span>
        <button class="del-btn" @click.stop="chat.deleteConversation(conv.id)" aria-label="删除对话" title="删除">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
        </button>
      </div>
      <div v-if="chat.conversations.length === 0" class="empty-hint">暂无对话记录</div>
    </div>
  </aside>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'

const chat = useChatStore()
const editingId = ref(null)
const editTitle = ref('')
const renameInputRef = ref(null)

async function newChat() {
  chat.currentConvId = null
  chat.messages = []
}

function startRename(conv) {
  editingId.value = conv.id
  editTitle.value = conv.title
  nextTick(() => {
    const inputs = renameInputRef.value
    const el = Array.isArray(inputs) ? inputs[0] : inputs
    el?.focus()
    el?.select()
  })
}

function finishRename(convId) {
  if (!editingId.value) return
  const trimmed = editTitle.value.trim()
  editingId.value = null
  if (trimmed && trimmed !== chat.conversations.find(c => c.id === convId)?.title) {
    chat.renameConversation(convId, trimmed)
  }
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-right: 1px solid #f0f0f0;
}

.sidebar-top {
  padding: 16px 14px 12px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 0;
  border-radius: 28px;
  background: #fff;
  color: #333;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
  border: 1px solid #eee;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.09);
  border-color: #ddd;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 10px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 2px;
}

.conv-item:hover { background: #f0f0f0; }

.conv-item.active {
  background: #e8ecff;
}

.conv-icon {
  flex-shrink: 0;
  color: #aaa;
}

.conv-item.active .conv-icon { color: #4f6ef7; }

.conv-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  color: #444;
}

.conv-item.active .conv-title { color: #4f6ef7; font-weight: 500; }

.rename-input {
  flex: 1;
  font-size: 13px;
  border: 1px solid #4f6ef7;
  border-radius: 4px;
  padding: 2px 6px;
  outline: none;
  min-width: 0;
}

.del-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #bbb;
  opacity: 0;
  transition: all 0.15s;
  flex-shrink: 0;
}

.conv-item:hover .del-btn { opacity: 1; }
.del-btn:hover { background: #fee; color: #e74c3c; }

.empty-hint {
  text-align: center;
  color: #ccc;
  font-size: 13px;
  padding: 48px 0;
}
</style>
