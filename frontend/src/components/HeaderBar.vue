<script setup>
import { ref } from 'vue'

// متغیرهای وضعیت هدر
const isSystemActive = ref(true)
const packetCount = ref(142)

function toggleSystem() {
  isSystemActive.value = !isSystemActive.value
}
</script>

<template>
  <header class="header-container">
    <div class="brand">
      <div class="logo-wrapper">
        <img src="../assets/main_logo.png" alt="AI Packet Inspector Logo" class="logo-img" />
        <span class="logo-placeholder"></span>
      </div>
      <div class="brand-titles">
        <h1 class="main-title">Ai<span class="highlight">powered</span></h1>
        <span class="sub-title">PACKET INSPECTOR</span>
      </div>
    </div>

    <!-- بخش کنترل و وضعیت سیستم -->
    <div class="controls">
      <!-- آمار پکت‌های پردازش‌شده -->
      <div class="stat-badge">
        <span class="stat-label">Queue:</span>
        <span class="stat-value">{{ packetCount }} pkts</span>
      </div>

      <!-- وضعیت زنده (Live Indicator) -->
      <div class="status-badge" :class="{ 'is-active': isSystemActive }">
        <span class="pulse-dot"></span>
        <span class="status-text">{{ isSystemActive ? 'INTERCEPTING' : 'PAUSED' }}</span>
      </div>

      <!-- دکمه سوییچ فعال/غیرفعال -->
      <button @click="toggleSystem" class="toggle-btn" :class="{ 'btn-active': isSystemActive }">
        {{ isSystemActive ? 'Pause Capture' : 'Resume Capture' }}
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
</style>