<template>
  <Teleport to="body">
    <div class="cz-modal" :class="{ on: visible }" :aria-hidden="!visible" @click="handleClick">
      <div class="add-scrim" @mousedown="onBackdropMouseDown" @click="onBackdropClick"></div>
      <div class="cz-card" role="dialog" aria-modal="true" :aria-labelledby="czTitleId">
        <header class="cz-hd">
          <button type="button" @click="handleBack" aria-label="返回">
            <svg viewBox="0 0 24 24" width="18" height="18"><path d="m14 6-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <h2 :id="czTitleId">{{ title }}</h2>
          <button type="button" @click="handleClose" aria-label="关闭">
            <svg viewBox="0 0 24 24" width="18" height="18"><path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </header>
        <div id="czBody">
          <!-- AI settings -->
          <template v-if="state.kind === 'ai'">
            <div class="cz-sec">
              <div class="cz-sec-t">挖空密度</div>
              <div class="cz-range">
                <span class="cz-end">疏</span>
                <div class="cz-track" ref="czTrackRef" @pointerdown="startDensityDrag">
                  <b></b>
                  <i :style="{ width: densityOffset + 'px' }"></i>
                  <button class="cz-knob" type="button" :style="{ left: densityOffset + 'px' }">{{ state.density }}%</button>
                </div>
                <span class="cz-end">密</span>
              </div>
            </div>
          </template>

          <!-- Rule settings -->
          <template v-else-if="state.kind === 'rule'">
            <div class="cz-sec">
              <div class="cz-sec-t">按内容（多选）</div>
              <div class="cz-box cz-grid">
                <button class="cz-chk" :class="{ on: state.rule.num }" type="button" @click="toggleRule('num')"><span class="cz-dot"></span><span>数字</span></button>
                <button class="cz-chk" :class="{ on: state.rule.year }" type="button" @click="toggleRule('year')"><span class="cz-dot"></span><span>年份</span></button>
                <button class="cz-chk" :class="{ on: state.rule.en }" type="button" @click="toggleRule('en')"><span class="cz-dot"></span><span>英文</span></button>
                <button class="cz-chk" :class="{ on: state.rule.custom }" type="button" @click="toggleRule('custom')"><span class="cz-dot"></span><span>自定义词语</span></button>
              </div>
              <div class="cz-extra" :class="{ on: state.rule.custom }">
                <input v-model="state.customWords" type="text" placeholder="多个词用逗号分隔" />
              </div>
            </div>
            <div class="cz-sec">
              <div class="cz-sec-t">按符号（多选）</div>
              <div class="cz-box cz-grid">
                <button class="cz-chk" :class="{ on: state.rule.paren }" type="button" @click="toggleRule('paren')"><span class="cz-dot"></span><span>(内容)</span></button>
                <button class="cz-chk" :class="{ on: state.rule.bracket }" type="button" @click="toggleRule('bracket')"><span class="cz-dot"></span><span>[内容]</span></button>
                <button class="cz-chk" :class="{ on: state.rule.corner }" type="button" @click="toggleRule('corner')"><span class="cz-dot"></span><span>【内容】</span></button>
                <button class="cz-chk" :class="{ on: state.rule.quote }" type="button" @click="toggleRule('quote')"><span class="cz-dot"></span><span>"内容"</span></button>
                <button class="cz-chk" :class="{ on: state.rule.symCustom }" type="button" @click="toggleRule('symCustom')"><span class="cz-dot"></span><span>自定义</span></button>
              </div>
              <div class="cz-extra" :class="{ on: state.rule.symCustom }">
                <input v-model="state.customSymbol" type="text" placeholder="输入要匹配的符号或文本" />
              </div>
            </div>
          </template>

          <!-- Template settings -->
          <template v-else-if="state.kind === 'tpl'">
            <div class="cz-sec">
              <div class="cz-sec-t">挖空单位</div>
              <div class="cz-radios">
                <button class="cz-radio" :class="{ on: state.unit === 'word' }" type="button" @click="state.unit = 'word'"><span class="cz-dot"></span><span>词</span></button>
                <button class="cz-radio" :class="{ on: state.unit === 'char' }" type="button" @click="state.unit = 'char'"><span class="cz-dot"></span><span>字</span></button>
                <button class="cz-radio" :class="{ on: state.unit === 'para' }" type="button" @click="state.unit = 'para'"><span class="cz-dot"></span><span>段</span></button>
              </div>
            </div>
            <div class="cz-sec">
              <div class="cz-sec-t">挖空间隔</div>
              <div class="cz-radios">
                <button class="cz-radio" :class="{ on: state.interval === 'fixed' }" type="button" @click="state.interval = 'fixed'"><span class="cz-dot"></span><span>固定间隔</span></button>
                <button class="cz-radio" :class="{ on: state.interval === 'random' }" type="button" @click="state.interval = 'random'"><span class="cz-dot"></span><span>随机间隔</span></button>
              </div>
            </div>
            <div class="cz-sec">
              <div class="cz-sec-t">间隔规则</div>
              <div class="cz-rule">
                每间隔 <input v-model.number="state.gap" type="number" min="1" max="20"> 个{{ state.unit === 'word' ? '词' : state.unit === 'para' ? '段' : '字' }}，
                隐藏 <input v-model.number="state.hide" type="number" min="1" max="20"> 个{{ state.unit === 'word' ? '词' : state.unit === 'para' ? '段' : '字' }}。
              </div>
            </div>
          </template>
        </div>
        <button class="cz-go" type="button" :disabled="saving" @click="handleGo">{{ saving ? '保存中…' : state.kind === 'chunk' ? '开始分块' : '立即挖空' }}</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { readConfigApi } from '@/utils/api'

const props = defineProps({
  visible: { type: Boolean, default: false },
  kind: { type: String, default: 'ai' }
})

const emit = defineEmits(['close', 'run', 'flash'])

const czTitleId = 'czTitle'
const czTrackRef = ref(null)
const backdropArmed = ref(false)

const state = reactive({
  kind: 'ai',
  density: 40,
  step: 'settings',
  scope: 'full',
  chapFrom: 0,
  chapTo: null,
  rule: {
    num: false, year: false, en: false, custom: false,
    paren: false, bracket: false, corner: false, quote: false, symCustom: false
  },
  customWords: '',
  customSymbol: '',
  unit: 'char',
  interval: 'fixed',
  gap: 3,
  hide: 3
})

const title = computed(() => {
  if (state.kind === 'chunk') return 'AI快速分块'
  if (state.kind === 'rule') return '规则挖空'
  if (state.kind === 'tpl') return '模版挖空'
  return 'AI快速挖空'
})

const densityOffset = ref(0)
const saving = ref(false)

watch(() => state.density, (val) => {
  const pct = Math.max(10, Math.min(90, val || 40))
  state.density = pct
  densityOffset.value = Math.round((pct - 10) / 80 * 200)
}, { immediate: true })

watch(() => props.visible, (val) => {
  if (val) {
    state.kind = props.kind
    state.step = 'settings'
    state.scope = 'full'
    state.chapTo = null
    // AI挖空：挖空密度从后端已保存的配置获取
    if (props.kind === 'ai') {
      readConfigApi.getConfigWordHollow().then(res => {
        const d = res && res.code === 0 && res.data ? Number(res.data.density) : NaN
        if (Number.isFinite(d)) state.density = Math.max(10, Math.min(90, d))
      }).catch(() => {})
    }
  }
})

function toggleRule(key) {
  state.rule[key] = !state.rule[key]
}

function startDensityDrag(e) {
  e.preventDefault()
  updateDensity(e.clientX)
  const move = (ev) => updateDensity(ev.clientX)
  const up = () => {
    document.removeEventListener('pointermove', move)
    document.removeEventListener('pointerup', up)
  }
  document.addEventListener('pointermove', move)
  document.addEventListener('pointerup', up)
}

function updateDensity(clientX) {
  const track = czTrackRef.value
  if (!track) return
  const r = track.getBoundingClientRect()
  const t = Math.max(0, Math.min(1, (clientX - r.left) / r.width))
  state.density = Math.round(10 + t * 80)
}

function onBackdropMouseDown(e) {
  backdropArmed.value = e.target === e.currentTarget && e.button === 0
}

function onBackdropClick(e) {
  const shouldClose = backdropArmed.value && e.target === e.currentTarget
  backdropArmed.value = false
  if (shouldClose) handleClose()
}

function handleClick(e) {
  if (e.target.closest('[data-cz-close]')) handleClose()
  if (e.target.closest('[data-cz-back]')) handleBack()
}

function handleClose() {
  emit('close', null)
}

function handleBack() {
  handleClose()
}

async function handleGo() {
  // Validate
  if (state.kind === 'rule') {
    const any = Object.values(state.rule).some(v => v)
    if (!any) { return }
  }
  // AI挖空：先调用接口保存挖空配置，随后直接执行（不再选择生效范围，只针对当前章节）
  if (state.kind === 'ai') {
    saving.value = true
    try {
      const res = await readConfigApi.updateWordHollow({
        hollowType: 1,
        density: state.density,
        keyWords: 0,
        wordUnit: 1,
        intervalType: 1,
        interval: '3',
        hide: '3'
      })
      if (!res || res.code !== 0) throw new Error((res && res.msg) || '保存配置失败')
    } catch (e) {
      emit('flash', (e && e.message) || '保存配置失败，请重试')
      return
    } finally {
      saving.value = false
    }
    emit('run', { ...state })
    return
  }
  // 规则/模版挖空：同样不再选择生效范围，直接执行（只针对当前章节）
  emit('run', { ...state })
}
</script>

<style scoped>
.add-scrim {
  position: absolute;
  inset: 0;
  background: rgba(22, 24, 29, 0.36);
}

.cz-modal {
  position: fixed;
  inset: 0;
  z-index: 470;
  display: none;
  align-items: center;
  justify-content: center;
}

.cz-modal.on {
  display: flex;
}

.cz-card {
  position: relative;
  width: 400px;
  max-width: calc(100% - 80px);
  background: var(--surface);
  border-radius: 18px;
  padding: 0 20px 18px;
  box-shadow: var(--shadow-lg);
  z-index: 1;
}

.cz-hd {
  display: flex;
  align-items: center;
  height: 52px;
  margin: 0 -8px 8px;
}

.cz-hd h2 {
  flex: 1;
  margin: 0;
  text-align: center;
  font-size: 16px;
  font-weight: 650;
}

.cz-hd button {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-2);
  flex: 0 0 32px;
}

.cz-hd button:hover {
  background: var(--bg-soft);
  color: var(--ink);
}

.cz-sec {
  margin: 0 0 16px;
}

.cz-sec-t {
  font-size: 13px;
  font-weight: 550;
  color: var(--ink);
  margin: 0 0 10px;
}

.cz-radios {
  display: flex;
  flex-wrap: wrap;
  gap: 18px 24px;
}

.cz-radio {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--ink);
  cursor: pointer;
}

.cz-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1.5px solid var(--line-strong);
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 18px;
}

.cz-radio.on .cz-dot,
.cz-chk.on .cz-dot {
  border-color: var(--ink);
}

.cz-radio.on .cz-dot::after,
.cz-chk.on .cz-dot::after {
  content: "";
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--ink);
}

.cz-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cz-range .cz-end {
  font-size: 13px;
  color: var(--ink-2);
  flex: 0 0 auto;
}

.cz-track {
  position: relative;
  flex: 1;
  height: 28px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.cz-track b {
  display: block;
  width: 100%;
  height: 4px;
  border-radius: 99px;
  background: var(--line);
  pointer-events: none;
}

.cz-track i {
  position: absolute;
  left: 0;
  top: 50%;
  height: 4px;
  margin-top: -2px;
  border-radius: 99px;
  background: var(--ink);
  pointer-events: none;
}

.cz-knob {
  position: absolute;
  top: 50%;
  width: 36px;
  height: 36px;
  margin: -18px 0 0 -18px;
  border-radius: 50%;
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: 0 4px 12px rgba(20, 30, 60, 0.12);
  font-size: 11px;
  font-weight: 700;
  color: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cz-box {
  background: var(--bg-plain);
  border-radius: 12px;
  padding: 4px 14px;
}

.cz-chk {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  font-size: 14px;
  color: var(--ink);
  cursor: pointer;
  width: 100%;
  text-align: left;
  background: transparent;
}

.cz-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}

.cz-extra {
  display: none;
  padding: 0 0 12px 28px;
}

.cz-extra.on {
  display: block;
}

.cz-extra input {
  width: 100%;
  height: 34px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface);
  font: inherit;
  font-size: 13px;
  color: var(--ink);
  outline: none;
}

.cz-rule {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 12px 14px;
  background: var(--bg-plain);
  border-radius: 12px;
  font-size: 14px;
  color: var(--ink);
}

.cz-rule input {
  width: 44px;
  height: 32px;
  text-align: center;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface);
  font: inherit;
  font-size: 14px;
  font-weight: 650;
  color: var(--ink);
}

.cz-go {
  display: block;
  width: 100%;
  height: 44px;
  margin-top: 8px;
  border-radius: 10px;
  background: var(--btn);
  color: #fff;
  font-size: 15px;
  font-weight: 650;
}

.cz-go:hover {
  background: var(--btn-hover);
}

.cz-go:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>