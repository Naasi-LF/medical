<template>
  <div :class="['message', message.role]">
    <div class="msg-wrapper">
      <!-- User message -->
      <div v-if="message.role === 'user'" class="user-bubble">
        {{ message.content }}
      </div>

      <!-- Assistant message -->
      <div v-else class="assistant-block">
        <!-- Thinking trace -->
        <div v-if="message.thinking" class="thinking-section">
          <button class="thinking-toggle" @click="showThinking = !showThinking">
            <svg :class="{ rotated: showThinking }" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M5 3l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="thinking-dot" v-if="streaming && !message.content"></span>
            <span>{{ streaming && !message.content ? '思考中...' : '思考过程' }}</span>
          </button>
          <div v-show="showThinking" class="thinking-content">{{ message.thinking }}</div>
        </div>

        <!-- Streaming indicator (no thinking yet, no answer yet) -->
        <div v-if="streaming && !message.thinking && !message.content" class="thinking-section">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- Answer -->
        <div v-if="message.content" class="answer-content" v-html="renderMarkdown(message.content)"></div>

        <!-- References -->
        <div v-if="message.references && message.references.length" class="references">
          <div class="ref-label">参考来源</div>
          <div class="ref-list">
            <div v-for="ref in message.references" :key="ref.idx" class="ref-item">
              <span class="ref-idx">[{{ ref.idx }}]</span>
              <span class="ref-title">{{ ref.title }}</span>
              <a v-if="ref.source" :href="ref.source" target="_blank" class="ref-link">查看</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

const props = defineProps({
  message: { type: Object, required: true },
  streaming: { type: Boolean, default: false },
})

const showThinking = ref(false)

function renderMarkdown(text) {
  return marked.parse(text)
}
</script>

<style scoped>
.message {
  padding: 4px 0;
}

.msg-wrapper {
  max-width: 768px;
  margin: 0 auto;
  padding: 0 24px;
}

/* User */
.message.user .msg-wrapper {
  display: flex;
  justify-content: flex-end;
}

.user-bubble {
  background: var(--user-bubble);
  color: #fff;
  padding: 10px 16px;
  border-radius: 18px 18px 4px 18px;
  max-width: 75%;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Assistant */
.assistant-block {
  max-width: 100%;
}

.thinking-section {
  margin-bottom: 8px;
}

.thinking-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 4px 0;
  transition: var(--transition);
}

.thinking-toggle:hover { color: var(--text); }

.thinking-toggle svg {
  transition: transform 0.2s;
}

.thinking-toggle svg.rotated {
  transform: rotate(90deg);
}

.thinking-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse-dot 1.2s infinite ease-in-out;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1); }
}

.thinking-content {
  color: #666;
  font-size: 13px;
  line-height: 1.6;
  border-left: 2px solid #e0e3ea;
  padding: 8px 12px;
  margin-top: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.answer-content {
  font-size: 14px;
  line-height: 1.75;
  color: var(--text);
  word-break: break-word;
}

/* ── Markdown rendered elements ── */

.answer-content :deep(h1),
.answer-content :deep(h2),
.answer-content :deep(h3) {
  margin: 16px 0 8px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
}

.answer-content :deep(h1) { font-size: 20px; }
.answer-content :deep(h2) { font-size: 17px; }
.answer-content :deep(h3) { font-size: 15px; }

.answer-content :deep(p) {
  margin: 6px 0;
}

.answer-content :deep(strong) {
  font-weight: 600;
}

.answer-content :deep(em) {
  font-style: italic;
}

.answer-content :deep(ul),
.answer-content :deep(ol) {
  margin: 6px 0;
  padding-left: 1.6em;
}

.answer-content :deep(li) {
  margin: 3px 0;
}

.answer-content :deep(li > ul),
.answer-content :deep(li > ol) {
  margin: 2px 0;
}

.answer-content :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 12px;
  border-left: 3px solid var(--border);
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.02);
  border-radius: 0 4px 4px 0;
}

.answer-content :deep(code) {
  font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  background: rgba(0, 0, 0, 0.05);
  padding: 1px 5px;
  border-radius: 3px;
}

.answer-content :deep(pre) {
  margin: 8px 0;
  padding: 12px 14px;
  background: #f6f8fa;
  border-radius: 6px;
  overflow-x: auto;
}

.answer-content :deep(pre code) {
  background: none;
  padding: 0;
}

.answer-content :deep(a) {
  color: var(--accent);
  text-decoration: none;
}

.answer-content :deep(a:hover) {
  text-decoration: underline;
}

.answer-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 12px 0;
}

.answer-content :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
  font-size: 13px;
}

.answer-content :deep(th),
.answer-content :deep(td) {
  border: 1px solid var(--border);
  padding: 6px 10px;
  text-align: left;
}

.answer-content :deep(th) {
  background: rgba(0, 0, 0, 0.03);
  font-weight: 600;
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: bounce-dot 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce-dot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* References */
.references {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.ref-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.ref-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ref-item {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.ref-idx {
  color: var(--accent);
  font-weight: 600;
  flex-shrink: 0;
}

.ref-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ref-link {
  color: var(--accent);
  font-size: 11px;
  flex-shrink: 0;
}

.ref-link:hover { text-decoration: underline; }
</style>
