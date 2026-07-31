<script setup>
import { ref } from 'vue'
import HeaderBar from './components/HeaderBar.vue'
import PacketTable from './components/PacketTable.vue'
import PacketInspector from './components/PacketInspector.vue'

const currentSelectedPacket = ref(null)

function onPacketSelected(packet) {
  currentSelectedPacket.value = packet
}
</script>

<template>
  <div class="dashboard-container">

    <HeaderBar />

    <main class="main-zone">
      <section class="table-zone">
        <PacketTable @select-packet="onPacketSelected" />
      </section>

      <aside class="inspector-zone">
        <PacketInspector :packet="currentSelectedPacket" />
      </aside>
    </main>

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
}

.table-zone {
  flex: 2;
  background: #15102a;
  border: 1px solid #2e2348;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.inspector-zone {
  flex: 1;
  background: #15102a;
  border: 1px solid #2e2348;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}
</style>