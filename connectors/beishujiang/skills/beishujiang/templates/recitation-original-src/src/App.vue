<script setup>
/**
 * 独立演示壳 — 原项目中 App.vue 的极简版,只为驱动阅读页(RecitePage):
 * - 提供它需要的 props(categories/folderGroups/doc/currentDoc 等)
 * - 处理它抛出的事件(flash 提示 / 未保存弹框 / 保存结果 / 新建材料)
 * - 复刻原项目的 fit() 视口缩放逻辑(按 1440px 设计稿)
 * 阅读页本身保留原项目视觉与翻转/挖空交互，仅适配导入页码和安全富文本。
 */
import { ref, computed, reactive, onMounted } from 'vue'
import RecitePage from './views/RecitePage.vue'
import ToastMessage from './components/ToastMessage.vue'
import { getInjectedMaterial } from './utils/recitation-material'

const injectedMaterial = getInjectedMaterial()

// ──────────────── 文档数据(原项目由后端 + App.vue 维护,这里本地维护) ────────────────
const DOCS = reactive({
  'demo-book-1': {
    title: '岳阳楼记 + 数学笔记(演示文档)',
    meta: '演示 / 3章',
    html: null
  }
})

if (injectedMaterial) {
  DOCS['imported-book'] = {
    title: injectedMaterial.title,
    meta: `PDF / ${injectedMaterial.pages.length} 页`,
    html: null
  }
}

const currentDoc = ref(injectedMaterial ? 'imported-book' : 'demo-book-1')
const autoEdit = ref(false)
const railOff = ref(false)
const unsavedDocIds = ref(new Set())

// RecitePage 必传的侧栏 props(演示壳无侧栏,给最小合法值)
const categories = ref([{ name: '全部', count: 1, icon: 'grid' }])
const folderGroups = ref([])
const homeCat = ref('全部')

const currentDocData = computed(() => (currentDoc.value && DOCS[currentDoc.value]) || null)
const currentDocIsNew = computed(() => unsavedDocIds.value.has(currentDoc.value))

// ──────────────── Toast(对应原项目 flash) ────────────────
const toastVisible = ref(false)
const toastMessage = ref('')
let toastTimer = null
function flash(msg) {
  toastMessage.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 1800)
}

// ──────────────── 新建材料(open-add) ────────────────
let addSeq = 0
function handleOpenAdd() {
  addSeq++
  const id = 'local-' + Date.now().toString(36)
  DOCS[id] = {
    title: `手动输入 · 新背诵材料 ${addSeq}`,
    meta: '新文档',
    html: '<section class="d-sec"><p><br></p></section>'
  }
  unsavedDocIds.value = new Set(unsavedDocIds.value).add(id)
  currentDoc.value = id
  autoEdit.value = true
  flash('已添加,自动进入编辑模式')
}

// ──────────────── 未保存弹框(对应原项目 DocModal 'unsaved') ────────────────
const reciteRef = ref(null)
const unsavedVisible = ref(false)
function handleOpenUnsaved() {
  unsavedVisible.value = true
}
function handleUnsavedSave() {
  unsavedVisible.value = false
  reciteRef.value?.confirmSave()
}
function handleUnsavedDiscard() {
  unsavedVisible.value = false
  reciteRef.value?.cancelEdit()
}

// ──────────────── 保存结果回写(save-book:本地临时 id → 服务端 id) ────────────────
function handleSaveBook({ from, id }) {
  if (!from || !id) return
  const next = new Set(unsavedDocIds.value)
  next.delete(from)
  unsavedDocIds.value = next
  if (DOCS[from]) {
    DOCS[id] = DOCS[from]
    delete DOCS[from]
  }
  currentDoc.value = id
}

// ──────────────── 其余事件:演示壳里无对应页面,给提示即可 ────────────────
function handleToggleRail() {
  railOff.value = !railOff.value
}
function handleSaveDoc(html) {
  if (currentDoc.value && DOCS[currentDoc.value]) {
    DOCS[currentDoc.value].html = html
  }
}

// ──────────────── fit() 缩放(与原项目 App.vue 一致) ────────────────
function fit() {
  const app = document.getElementById('app-root')
  if (!app) return
  const avail = window.innerWidth
  if (avail < 1440) {
    // 窄屏:缩放适配
    const s = avail / 1440
    app.style.transform = `scale(${s})`
    app.style.transformOrigin = 'top left'
    app.style.width = '1440px'
    app.style.height = (window.innerHeight / s) + 'px'
  } else {
    // 宽屏:直接铺满,不缩放
    app.style.transform = 'none'
    app.style.width = '100%'
    app.style.height = '100vh'
  }
}

onMounted(() => {
  fit()
  window.addEventListener('resize', fit)
})
</script>

<template>
  <div id="app-root" class="frame">
    <RecitePage
      ref="reciteRef"
      :categories="categories"
      :folder-groups="folderGroups"
      :home-cat="homeCat"
      :current-doc="currentDoc"
      :rail-off="railOff"
      :doc="currentDocData"
      :is-new-doc="currentDocIsNew"
      :auto-edit="autoEdit"
      @open-add="handleOpenAdd"
      @open-dlapp="flash('独立演示版,未包含下载页')"
      @toggle-rail="handleToggleRail"
      @row-action="() => {}"
      @flash="flash"
      @go-home="flash('独立演示版仅包含阅读页')"
      @open-share="flash('独立演示版,未包含分享')"
      @open-feedback="flash('独立演示版,未包含反馈')"
      @open-unsaved="handleOpenUnsaved"
      @save-doc="handleSaveDoc"
      @save-book="handleSaveBook"
      @edit-entered="autoEdit = false"
    />

    <!-- 未保存弹框(对应原项目 DocModal 'unsaved') -->
    <div class="mini-modal-mask" v-if="unsavedVisible" @click.self="unsavedVisible = false">
      <div class="mini-modal" role="dialog" aria-modal="true">
        <div class="mini-modal-title">有未保存的修改</div>
        <div class="mini-modal-text">离开编辑模式前,是否保存当前修改?</div>
        <div class="mini-modal-acts">
          <button class="mini-btn" type="button" @click="unsavedVisible = false">取消</button>
          <button class="mini-btn" type="button" @click="handleUnsavedDiscard">不保存</button>
          <button class="mini-btn primary" type="button" @click="handleUnsavedSave">保存</button>
        </div>
      </div>
    </div>

    <ToastMessage :visible="toastVisible" :message="toastMessage" />
  </div>
</template>

<style>
/* ===== 与原项目 App.vue 全局样式一致的部分 ===== */
.frame {
  width: 100%;
  height: 100vh;
  background: var(--bg);
  position: relative;
  overflow: hidden;
}

#app-root {
  display: flex;
  flex-direction: column;
}

/* Make app-root fill the full height */
.frame > .shell {
  width: 100%;
  height: 100%;
}

/* ===== 演示壳自带的未保存弹框样式 ===== */
.mini-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 18, 25, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.mini-modal {
  background: var(--paper, #fff);
  border-radius: 14px;
  box-shadow: 0 18px 48px rgba(15, 18, 25, 0.22);
  padding: 26px 28px 20px;
  width: 340px;
  max-width: calc(100vw - 48px);
}

.mini-modal-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--ink, #22252e);
  margin-bottom: 10px;
}

.mini-modal-text {
  font-size: 13px;
  color: var(--ink-2, #5c6070);
  line-height: 1.7;
}

.mini-modal-acts {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 22px;
}

.mini-btn {
  border: 1px solid var(--line, #d9dbe4);
  background: transparent;
  color: var(--ink, #22252e);
  border-radius: 9px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
}

.mini-btn:hover {
  border-color: var(--ink, #22252e);
}

.mini-btn.primary {
  background: var(--accent, #3358ff);
  border-color: var(--accent, #3358ff);
  color: #fff;
}
</style>
