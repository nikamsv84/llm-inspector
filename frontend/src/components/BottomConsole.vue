<template>
  <div class="console-container">
    <div class="console-title">🖥️ Bottom Console</div>
    <div class="console-placeholder">
      Response logs and AI analysis will appear here.
    </div>
  </div>
</template>

<style scoped>
.console-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.console-title {
  font-size: 0.85rem;
  color: #c084fc;
  font-weight: 600;
  margin-bottom: 8px;
}

.console-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 0.8rem;
  border: 1px dashed #2e2348;
  border-radius: 8px;
}
</style>