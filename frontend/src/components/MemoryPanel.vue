<template>
  <div class="memory-panel">
    <div class="panel-header">
      <h3>个人健康档案</h3>
      <button class="close-btn" @click="$emit('close')">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      </button>
    </div>

    <div class="panel-body">
      <!-- Manual input -->
      <div class="input-section">
        <p class="hint">告诉我你的个人信息，我会记住并提供更精准的建议</p>
        <div class="input-row">
          <input v-model="infoText" placeholder="例如：我是60岁老人，有慢性胃炎" @keydown.enter="submitInfo" />
          <button @click="submitInfo" :disabled="!infoText.trim() || saving" class="save-btn">
            {{ saving ? '...' : '记住' }}
          </button>
        </div>
      </div>

      <!-- Entities -->
      <div class="section" v-if="entities.length">
        <h4>已记录的信息</h4>
        <div v-for="ent in entities" :key="ent.id" class="entity-card">
          <div class="entity-info">
            <span class="entity-type">{{ typeLabel(ent.entity_type) }}</span>
            <span class="entity-name">{{ ent.entity_name }}</span>
            <span v-if="Object.keys(ent.properties).length" class="entity-props">
              {{ formatProps(ent.properties) }}
            </span>
          </div>
          <button class="remove-btn" @click="removeEntity(ent.id)" title="删除">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>
      </div>

      <!-- Relations -->
      <div class="section" v-if="relations.length">
        <h4>关系图谱</h4>
        <div v-for="rel in relations" :key="rel.id" class="relation-card">
          <span>{{ rel.source }}</span>
          <span class="rel-arrow">→ {{ rel.relation }} →</span>
          <span>{{ rel.target }}</span>
          <button class="remove-btn" @click="removeRelation(rel.id)" title="删除">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>
      </div>

      <div v-if="!entities.length && !relations.length && !loading" class="empty">
        还没有记录任何信息
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

defineEmits(['close'])

const entities = ref([])
const relations = ref([])
const infoText = ref('')
const saving = ref(false)
const loading = ref(true)

const typeLabels = {
  age_group: '年龄段',
  gender: '性别',
  condition: '疾病/症状',
  medication: '用药',
  allergy: '过敏',
  habit: '生活习惯',
  family_history: '家族病史',
  preference: '偏好',
}

function typeLabel(t) { return typeLabels[t] || t }

function formatProps(props) {
  return Object.entries(props)
    .map(([k, v]) => `${k}: ${v}`)
    .join(', ')
}

async function fetchMemory() {
  loading.value = true
  try {
    const { data } = await api.get('/memory')
    entities.value = data.entities
    relations.value = data.relations
  } finally {
    loading.value = false
  }
}

async function submitInfo() {
  if (!infoText.value.trim() || saving.value) return
  saving.value = true
  try {
    await api.post('/memory/extract', { text: infoText.value })
    infoText.value = ''
    await fetchMemory()
  } finally {
    saving.value = false
  }
}

async function removeEntity(id) {
  await api.delete(`/memory/entity/${id}`)
  entities.value = entities.value.filter((e) => e.id !== id)
}

async function removeRelation(id) {
  await api.delete(`/memory/relation/${id}`)
  relations.value = relations.value.filter((r) => r.id !== id)
}

onMounted(fetchMemory)
</script>

<style scoped>
.memory-panel {
  width: 320px;
  min-width: 320px;
  border-left: 1px solid var(--border);
  background: var(--panel);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}

.panel-header h3 {
  font-size: 15px;
  font-weight: 700;
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--text-secondary);
  transition: var(--transition);
}

.close-btn:hover { background: var(--bg); }

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.input-section {
  margin-bottom: 20px;
}

.hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.5;
}

.input-row {
  display: flex;
  gap: 6px;
}

.input-row input {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  font-size: 13px;
}

.input-row input:focus {
  border-color: var(--accent);
}

.save-btn {
  padding: 8px 14px;
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: var(--transition);
}

.save-btn:hover:not(:disabled) { background: var(--accent-hover); }
.save-btn:disabled { opacity: 0.5; }

.section {
  margin-bottom: 16px;
}

.section h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.entity-card, .relation-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
  font-size: 13px;
}

.entity-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.entity-type {
  padding: 2px 6px;
  background: var(--accent-light);
  color: var(--accent);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.entity-name {
  font-weight: 500;
}

.entity-props {
  color: var(--text-secondary);
  font-size: 11px;
}

.rel-arrow {
  color: var(--accent);
  font-size: 12px;
  margin: 0 4px;
}

.remove-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: var(--text-secondary);
  opacity: 0;
  transition: var(--transition);
  flex-shrink: 0;
}

.entity-card:hover .remove-btn,
.relation-card:hover .remove-btn { opacity: 1; }
.remove-btn:hover { color: var(--danger); background: #fee; }

.empty {
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 40px 0;
}
</style>
