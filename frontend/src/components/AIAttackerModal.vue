<template>
  <div class="modal-overlay">
    <div class="modal-box">

      <!-- Close button with X icon -->
      <button class="close-btn" @click="$emit('close')">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>

      <h3>AI Attacker</h3>
      <p>Payload generator will appear here
      coming soon....</p>
    </div>
  </div>
</template>

<script setup>
// Define the event emitted to the parent component to close the modal
defineEmits(['close']);
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-box {
  position: relative; /* Required for absolute positioning of the close button */
  background: #15102a;
  border: 1px solid #2e2348;
  border-radius: 12px;
  padding: 24px;
  min-width: 400px;
  color: #e2e8f0;
}

/* Close button specific styles */
.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: transparent;
  border: none;
  color: #9976c9;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

/* Hover effect for the close button */
.close-btn:hover {
  color: #8622de; /* Turns white */
  background: rgba(255, 255, 255, 0.1); /* Slight background highlight */
}
</style>