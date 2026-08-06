<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const isSystemActive = ref(true)
const packetCount = ref(0)

let socket = null
let reconnectTimeout = null
const RECONNECT_DELAY = 2000 // ms

// 1. Fetch initial status and queue count from FastAPI (one-time snapshot on load)
async function fetchCurrentStatus() {
  try {
    const response = await fetch('http://localhost:8000/api/v1/system/status', {
      cache: 'no-store'
    })
    const data = await response.json()

    // data.status is the `is_paused` value from get_dashboard_status()
    // If status (is_paused) is true -> system is paused (isSystemActive = false)
    isSystemActive.value = !data.status

    // Initial queue count snapshot; live updates take over from here via WebSocket
    packetCount.value = data.pending_intercepts
  } catch (error) {
    console.error('Failed to fetch initial status:', error)
  }
}

// 2. Toggle status when the user clicks the button
async function toggleSystem() {
  try {
    const response = await fetch('http://localhost:8000/api/v1/system/toggle-pause', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const data = await response.json()

    // Assuming toggle-pause returns { "is_paused": boolean } or similar boolean result
    // If it returns an object like { "is_paused": true }, use data.is_paused or data directly
    const pausedState = typeof data === 'object' && data !== null ? (data.is_paused ?? data.status) : data
    isSystemActive.value = !pausedState

  } catch (error) {
    console.error('Failed to send toggle status request:', error)
  }
}

// 3. Live packet count via WebSocket (backend broadcasts one message per new packet
//    from notify_new_packet() in dashboard/api.py -> ConnectionManager.broadcast)
function connectWebSocket() {
  socket = new WebSocket('ws://localhost:8000/ws/packets')

  socket.onopen = () => {
    console.log('[ws] connected to /ws/packets')
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
  }

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)

      // If the backend ever sends an explicit count/queue size, prefer that;
      // otherwise treat each message as "one new packet arrived".
      if (payload && typeof payload.pending_intercepts === 'number') {
        packetCount.value = payload.pending_intercepts
      } else if (payload && typeof payload.count === 'number') {
        packetCount.value = payload.count
      } else {
        packetCount.value += 1
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

onMounted(() => {
  fetchCurrentStatus()
  connectWebSocket()
})

onUnmounted(() => {
  if (reconnectTimeout) clearTimeout(reconnectTimeout)
  if (socket) {
    socket.onclose = null // don't trigger reconnect on manual unmount
    socket.close()
  }
})
</script>

<template>
  <header class="header-container">
    <div class="brand">
      <div class="logo-wrapper">
        <img src="../assets/main_logo.png" alt="AI Packet Inspector Logo" class="logo-img" />
        <span class="logo-placeholder"></span>
      </div>
      <div class="brand-titles">
        <h1 class="main-title">LLM<span class="highlight">inspector</span></h1>
        <span class="sub-title">PACKET INSPECTOR FOCUSED ON LLM APIS</span>
      </div>
    </div>

    <div class="controls">
      <div class="stat-badge">
        <span class="stat-label">Queue:</span>
        <span class="stat-value">{{ packetCount }} pkts</span>
      </div>

      <div class="status-badge" :class="{ 'is-active': isSystemActive }">
        <span class="pulse-dot"></span>
        <span class="status-text">{{ isSystemActive ? 'INTERCEPTING' : 'PAUSED' }}</span>
      </div>

      <button @click="toggleSystem" class="toggle-btn" :class="{ 'btn-active': isSystemActive }">
        {{ isSystemActive ? 'Pause Capture' : 'Resume Capture' }}
      </button>
      <button class="gen-report-btn">
      Generate Report
      </button>
    </div>
  </header>
</template>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #15102a;
  border: 1px solid #2e2348;
  border-radius: 12px;
  padding: 12px 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

/* Brand styling */
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-wrapper {
  width: 44px;
  height: 44px;
  background: #23193e;
  border: 1px solid #a855f7;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 12px rgba(168, 85, 247, 0.3);
}

.logo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: screen;
}

.logo-placeholder {
  font-size: 1.4rem;
}

.brand-titles {
  display: flex;
  flex-direction: column;
}

.main-title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.highlight {
  color: #c084fc; /* Lilac accent */
}

.sub-title {
  font-size: 0.65rem;
  font-weight: 700;
  color: #a855f7;
  letter-spacing: 2px;
}

/* Controls & Status */
.controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-badge {
  background: #1e1738;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #3b2d5e;
  font-size: 0.85rem;
}

.stat-label {
  color: #94a3b8;
  margin-right: 6px;
}

.stat-value {
  color: #e2e8f0;
  font-weight: 600;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.status-badge.is-active {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #34d399;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #ef4444;
}

.status-badge.is-active .pulse-dot {
  background-color: #10b981;
  box-shadow: 0 0 8px #10b981;
}

/* Toggle button */
.toggle-btn {
  background: #2e2348;
  color: #e2e8f0;
  border: 1px solid #4c3a75;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: #3b2d5e;
  border-color: #a855f7;
}

.toggle-btn.btn-active {
  border-color: #34d399;
}

@keyframes report-pulse {
  0%, 100% {
    border-color: #6b21a8;
    box-shadow: 0 0 4px rgba(147, 51, 234, 0.25);
  }
  50% {
    border-color: #a855f7;
    box-shadow: 0 0 10px rgba(147, 51, 234, 0.5);
  }
}

.gen-report-btn {
  background: rgba(147, 51, 234, 0.15);
  color: #c4b5fd;
  border: 1px solid #6b21a8;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  animation: report-pulse 2.5s ease-in-out infinite;
}

.gen-report-btn:hover {
  animation-play-state: paused;
  opacity: 0.85;
}
</style>