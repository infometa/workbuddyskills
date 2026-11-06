<template>
  <Teleport to="body">
    <div class="ai-mask" :class="{ on: visible }" :hidden="!visible" :aria-hidden="!visible">
      <div class="ai-mask-card" role="status" aria-live="polite">
        <div class="ai-loader" aria-hidden="true">
          <span class="ring"></span>
          <span class="ring2 ring"></span>
          <span class="core"></span>
        </div>
        <p class="ai-mask-text" :class="{ swap: animating }">{{ text }}</p>
        <div class="ai-mask-bar" aria-hidden="true">
          <i :style="{ animation: barAnim }"></i>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  text: { type: String, default: '正在进行分析…' },
  duration: { type: Number, default: 2700 }
})

const animating = ref(false)
const barAnim = computed(() => {
  return props.visible ? `aiBarFill ${props.duration}ms linear forwards` : 'none'
})
</script>

<style scoped>
.ai-mask {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 480;
  align-items: center;
  justify-content: center;
  background: rgba(242, 243, 245, 0.72);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  user-select: none;
  cursor: progress;
}

.ai-mask.on {
  display: flex;
}

.ai-mask-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 260px;
  padding: 28px 36px 24px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: 0 16px 40px rgba(20, 30, 60, 0.12);
}

.ai-loader {
  position: relative;
  width: 56px;
  height: 56px;
  margin: 0 0 18px;
}

.ai-loader .ring {
  position: absolute;
  inset: 0;
  border: 2.5px solid var(--accent-weak);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.85s linear infinite;
}

.ai-loader .ring2 {
  inset: 9px;
  border-width: 2px;
  border-top-color: transparent;
  border-right-color: var(--accent);
  animation-duration: 1.35s;
  animation-direction: reverse;
}

.ai-loader .core {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
  background: var(--accent);
  border-radius: 50%;
  animation: aiPulse 1.15s ease-in-out infinite;
}

.ai-mask-text {
  margin: 0;
  min-height: 1.45em;
  font-size: 15px;
  font-weight: 650;
  color: var(--ink);
  letter-spacing: 0.02em;
  text-align: center;
}

.ai-mask-text.swap {
  animation: aiTextIn 0.42s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.ai-mask-bar {
  width: 176px;
  height: 3px;
  margin: 16px 0 0;
  background: var(--line);
  border-radius: 99px;
  overflow: hidden;
}

.ai-mask-bar i {
  display: block;
  height: 100%;
  width: 0;
  background: var(--accent);
  border-radius: 99px;
}
</style>