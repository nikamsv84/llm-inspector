<script setup>
import { ref } from 'vue'
import HeaderBar from './components/HeaderBar.vue'
import PacketTable from './components/PacketTable.vue'
import PacketInspector from './components/PacketInspector.vue'
import BottomConsole from './components/BottomConsole.vue'
import AIAttackerModal from './components/AIAttackerModal.vue'

const currentSelectedPacket = ref(null)
const showAIModal = ref(false)

function onPacketSelected(packet) {
  currentSelectedPacket.value = packet
}

async function onInspectorAction(payload) {
  const { id, action, modified_body, modified_headers, modified_method, modified_path } = payload;

  let apiPayload = {
    request_id: id,
    action: action
  };

  if (action === 'modified') {
    apiPayload.modified_data = {
      method: modified_method,
      path: modified_path,
      headers: modified_headers,
      body: modified_body
    }
  }

  try {
    const response = await fetch('http://localhost:8000/api/v1/intercept/release', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(apiPayload)
    });

    if (response.ok) {
      console.log(`✅ Action '${action}' sent to backend for packet #${id}`);
    } else {
      console.error('❌ Backend returned an error:', response.statusText);
    }
  } catch (error) {
    console.error('❌ Error sending action to backend:', error);
  }
}
</script>

<template>
  <div class="dashboard-container">

    <HeaderBar />

    <main class="main-zone">
      <div class="left-column">
        <section class="table-zone">
          <PacketTable @select-packet="onPacketSelected" />
        </section>

        <section class="console-zone">
          <BottomConsole />
        </section>
      </div>

      <aside class="inspector-zone">
        <PacketInspector
          :packet="currentSelectedPacket"
          @open-ai-modal="showAIModal = true"
          @action="onInspectorAction"
        />
      </aside>
    </main>

    <AIAttackerModal v-if="showAIModal" @close="showAIModal = false" />

  </div>
</template>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #0b0914;
  color: #e2e8f0;
  font-family: 'Inter', system-ui, sans-serif;
  padding: 16px;
  gap: 16px;
  box-sizing: border-box;
}

.main-zone {
  display: flex;
  flex: 1;
  gap: 16px;
  overflow: hidden;
  min-height: 0;
}

.left-column {
  display: flex;
  flex-direction: column;
  flex: 2;
  gap: 16px;
  min-height: 0;
}

.table-zone {
  flex: 3;
  background: #15102a;
  border: 1px solid #2e2348;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.console-zone {
  flex: 4;
  background: #15102a;
  border: 1px solid #2e2348;
  border-radius: 8px;
  padding: 16px;
  overflow: hidden;
  min-height: 0;
}

.inspector-zone {
  flex: 2;
  background: #15102a;
  border: 1px solid #2e2348;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>