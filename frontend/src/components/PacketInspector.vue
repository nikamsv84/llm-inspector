<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  packet: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['action', 'open-ai-modal'])
function openAIModal() {
  emit('open-ai-modal')
}

const editableFields = ref({
  method: '',
  path: '',
  http_version: '',
  query_params: '',
  target_host: '',
  target_port: ''
})

const bodyValue = ref('')

const selectedField = ref(null)
const editingValue = ref('')

function initEditors() {
  if (!props.packet) return
  editableFields.value = {
    method: props.packet.method || '',
    path: props.packet.path || '',
    http_version: props.packet.http_version || 'HTTP/1.1',
    query_params: props.packet.query_params || '',
    target_host: props.packet.target_host || '',
    target_port: props.packet.target_port || ''
  }
  bodyValue.value = props.packet.body || ''
  selectedField.value = null
  editingValue.value = ''
}

watch(() => props.packet?.id, initEditors, { immediate: true })

const fieldLabels = {
  method: 'Method',
  path: 'Path',
  http_version: 'HTTP Version',
  query_params: 'Query Params',
  target_host: 'Host',
  target_port: 'Port'
}

function selectField(key) {
  selectedField.value = key
  editingValue.value = String(editableFields.value[key])
}

function applyFieldEdit() {
  if (!selectedField.value) return
  editableFields.value[selectedField.value] = editingValue.value
}

function handleAction(action) {
  emit('action', {
    id: props.packet.id,
    action,
    modified_method: editableFields.value.method,
    modified_path: editableFields.value.path,
    modified_http_version: editableFields.value.http_version,
    modified_query_params: editableFields.value.query_params,
    modified_target_host: editableFields.value.target_host,
    modified_target_port: editableFields.value.target_port,
    modified_body: bodyValue.value
  })
}
</script>

<template>
  <div class="inspector-container">
    <div class="inspector-header">
      <h3>🔍 Packet Inspector</h3>
      <span v-if="packet" class="pkt-id-tag">ID: #{{ packet.id }}</span>
    </div>

    <div v-if="!packet" class="empty-state">
      <span class="empty-icon">👈</span>
      <p>Select a packet from the live stream to inspect details.</p>
    </div>

    <div v-else class="inspector-content">
      <div class="editor-block">
        <div class="editor-title">Headers</div>
        <div class="summary-row">
          <div
            v-for="key in ['method', 'path', 'http_version', 'query_params', 'target_host', 'target_port']"
            :key="key"
            class="summary-item"
            :class="{ selected: selectedField === key }"
            @click="selectField(key)"
          >
            <span class="label">{{ fieldLabels[key] }}</span>
            <span
              class="value"
              :class="key === 'method' ? 'badge ' + editableFields[key].toLowerCase() : key === 'path' ? 'path' : ''"
            >
              {{ editableFields[key] || '—' }}
            </span>
          </div>
        </div>

        <textarea
          v-model="editingValue"
          class="edit-area"
          :disabled="selectedField === null"
          spellcheck="false"
          rows="2"
          :placeholder="selectedField ? 'Edit ' + fieldLabels[selectedField] : 'choose a field from the list above'"
        ></textarea>
        <button
          class="apply-btn"
          :disabled="selectedField === null"
          @click="applyFieldEdit"
        >
          Apply header
        </button>
        <button
        class="ai-generate-but" @click="openAIModal">
        Generate with AI
        </button>
      </div>

      <div class="editor-block">
        <div class="editor-title">Body</div>
        <textarea
          v-model="bodyValue"
          class="edit-area body-area"
          spellcheck="false"
          rows="6"
          placeholder="the body is empty"
        ></textarea>
      </div>

      <div class="action-bar">
        <button class="btn forward" @click="handleAction('forwarded')">
          Forward
        </button>
        <button class="btn modify" @click="handleAction('modified')">
          Send modified
        </button>
        <button class="btn drop" @click="handleAction('dropped')">
          Drop
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inspector-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.inspector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.inspector-header h3 {
  margin: 0;
  font-size: 1.05rem;
  color: #c084fc;
}

.pkt-id-tag {
  font-size: 0.75rem;
  background: #2e2348;
  color: #d8b4fe;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid #4c3a75;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #64748b;
  text-align: center;
  padding: 20px;
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}

.inspector-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 14px;
  overflow-y: auto;
}

.editor-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.editor-title {
  font-size: 0.7rem;
  color: #a855f7;
  font-weight: 700;
  text-transform: uppercase;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  background: #110d21;
  border-radius: 6px;
  border: 1px solid #1e1738;
  font-size: 0.8rem;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.summary-item:hover {
  border-color: #4c3a75;
}

.summary-item.selected {
  background: #2e2150;
  border-color: #c084fc;
}

.label {
  color: #94a3b8;
  font-size: 0.7rem;
  text-transform: uppercase;
}

.value {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.value.path { color: #38bdf8; font-family: monospace; font-size: 0.75rem; }
.value.badge.get { color: #60a5fa; }
.value.badge.post { color: #34d399; }
.value.badge.delete { color: #f87171; }
.value.badge.put { color: #facc15; }

.edit-area {
  background: #110d21;
  border: 1px solid #2e2348;
  border-radius: 6px;
  padding: 10px;
  font-family: 'Fira Code', monospace;
  font-size: 0.75rem;
  color: #e2e8f0;
  resize: vertical;
}

.edit-area:focus {
  outline: none;
  border-color: #7f77dd;
}

.edit-area:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.body-area {
  background: #1a1a1a;
  color: #9ca3af;
}

.apply-btn {
  align-self: flex-end;
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid #7f77dd;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.apply-btn:hover:not(:disabled) { opacity: 0.85; }
.apply-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.action-bar {
  display: flex;
  gap: 8px;
  margin-top: auto;
  padding-top: 8px;
}

.btn {
  flex: 1;
  padding: 10px;
  border-radius: 6px;
  border: none;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.btn:hover { opacity: 0.85; }

.btn.forward {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid #059669;
}

.btn.modify {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid #7f77dd;
}

.btn.drop {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid #dc2626;
}
@keyframes ai-pulse {
  0%, 100% {
    border-color: #a21caf;
    box-shadow: 0 0 4px rgba(217, 70, 239, 0.3);
  }
  50% {
    border-color: #e879f9;
    box-shadow: 0 0 10px rgba(217, 70, 239, 0.6);
  }
}

.ai-generate-but {
  background: rgba(217, 70, 239, 0.15);
  color: #e879f9;
  border: 1px solid #a21caf;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  animation: ai-pulse 2s ease-in-out infinite;
}

.ai-generate-but:hover {
  animation-play-state: paused;
  opacity: 0.85;
}
</style>