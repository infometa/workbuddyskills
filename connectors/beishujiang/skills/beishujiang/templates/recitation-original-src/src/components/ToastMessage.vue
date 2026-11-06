<template>
  <Teleport to="body">
    <div class="toast" :class="{ on: visible }">{{ message }}</div>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  message: { type: String, default: '' }
})
</script>

<style scoped>
.toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(22, 24, 29, 0.9);
  color: #fff;
  font-size: 13px;
  padding: 10px 16px;
  border-radius: 10px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s var(--ease);
  z-index: 1000;
}

.toast.on {
  opacity: 1;
}
</style>