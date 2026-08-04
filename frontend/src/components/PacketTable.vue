<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['select-packet'])
const selectedId = ref(null)
const packets = ref([])
let socket = null
let reconnectTimeout = null
const RECONNECT_DELAY = 3000
function connectWebSocket() {
  socket = new WebSocket('ws://localhost:8000/ws/packets')

  socket.onopen = () => {
    console.log('[ws] PacketTable connected')
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
  }

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.type === 'new_packet') {
        packets.value.unshift(payload.packet)
      }
    } catch (error) {
      console.error('[ws] failed to parse message:', error)
    }
  }

  socket.onerror = (error) => {
    console.error('[ws] error:', error)
  }

  socket.onclose = () => {
    console.warn('[ws] connection closed, retrying in', RECONNECT_DELAY, 'ms')
    socket = null
    reconnectTimeout = setTimeout(connectWebSocket, RECONNECT_DELAY)
  }
}

function handleSelect(packet) {
  selectedId.value = packet.id
  emit('select-packet', packet)
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (reconnectTimeout) clearTimeout(reconnectTimeout)
  if (socket) socket.close()
})
</script>

<template>
  <div class="table-container">
    <div class="table-header-title">
      <h3>📡 Live Packet Stream</h3>
      <span class="count-tag">{{ packets.length }} items</span>
    </div>

    <div class="table-wrapper">
      <table class="packet-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Time</th>
            <th>Method</th>
            <th>Path</th>
            <th>Status</th>
            <th>Threat</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="pkt in packets"
            :key="pkt.id"
            :class="{ 'selected-row': pkt.id === selectedId }"
            @click="handleSelect(pkt)"
          >
            <td class="id-cell">#{{ pkt.id }}</td>
            <td class="time-cell">{{ pkt.time }}</td>
            <td>
              <span class="method-badge" :class="pkt.method.toLowerCase()">
                {{ pkt.method }}
              </span>
            </td>
            <td class="path-cell">{{ pkt.path }}</td>
            <td>
              <span class="status-code" :class="'status-' + Math.floor(pkt.status / 100) + 'xx'">
                {{ pkt.status }}
              </span>
            </td>
            <td>
              <span class="risk-badge" :class="pkt.risk.toLowerCase()">
                {{ pkt.risk }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.table-header-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.table-header-title h3 {
  margin: 0;
  font-size: 1.05rem;
  color: #c084fc;
}

.count-tag {
  font-size: 0.75rem;
  background: #2e2348;
  color: #a855f7;
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid #4c3a75;
}

.table-wrapper {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #2e2348;
  border-radius: 8px;
  background: #110d21;
}

.packet-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.85rem;
  font-family: 'Fira Code', monospace, sans-serif;
}

.packet-table th {
  background-color: #191332;
  color: #94a3b8;
  padding: 10px 12px;
  font-weight: 600;
  border-bottom: 1px solid #2e2348;
  position: sticky;
  top: 0;
}

.packet-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #1e1738;
  color: #e2e8f0;
}

.packet-table tbody tr {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.packet-table tbody tr:hover {
  background-color: #1e1738;
}

.packet-table tbody tr.selected-row {
  background-color: #2e2150;
  border-left: 3px solid #c084fc;
}

.id-cell {
  color: #64748b;
}

.time-cell {
  color: #a1a1aa;
}

.path-cell {
  color: #f1f5f9;
}

/* Method Badges */
.method-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 6px;
  border-radius: 4px;
}
.method-badge.get { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.method-badge.post { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.method-badge.delete { background: rgba(239, 68, 68, 0.15); color: #f87171; }

/* Status Codes */
.status-code { font-weight: 600; }
.status-2xx { color: #34d399; }
.status-4xx { color: #fbbf24; }
.status-5xx { color: #f87171; }

/* Risk Badges */
.risk-badge {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}
.risk-badge.low { background: #142820; color: #4ade80; }
.risk-badge.medium { background: #33230a; color: #facc15; }
.risk-badge.high { background: #331118; color: #f87171; }
</style>