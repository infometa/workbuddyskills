<template>
  <span
    class="app-icon"
    :class="'app-icon--' + resolved"
    :style="boxStyle"
    aria-hidden="true"
    v-html="markup"
  />
</template>

<script setup>
import { computed } from 'vue'
import addSvg from '@/assets/icons/add.svg?raw'
import discoverSvg from '@/assets/icons/discover.svg?raw'
import articleSvg from '@/assets/icons/article.svg?raw'
import calendarSvg from '@/assets/icons/calendar.svg?raw'
import fileSvg from '@/assets/icons/file.svg?raw'
import text1Svg from '@/assets/icons/text-1.svg?raw'
import text2Svg from '@/assets/icons/text-2.svg?raw'
import editSvg from '@/assets/icons/edit.svg?raw'
import shareSvg from '@/assets/icons/share.svg?raw'
import eyeOnSvg from '@/assets/icons/eye-on.svg?raw'
import eyeOffSvg from '@/assets/icons/eye-off.svg?raw'
import menuCloseSvg from '@/assets/icons/menu-close.svg?raw'
import menuOpenSvg from '@/assets/icons/menu-open.svg?raw'
import clozeSvg from '@/assets/icons/cloze.svg?raw'
import chunkSvg from '@/assets/icons/chunk.svg?raw'
import boldSvg from '@/assets/icons/bold.svg?raw'
import strikeSvg from '@/assets/icons/strike.svg?raw'
import underlineSvg from '@/assets/icons/underline.svg?raw'
import italicSvg from '@/assets/icons/italic.svg?raw'
import colorSvg from '@/assets/icons/color.svg?raw'
import textStyleSvg from '@/assets/icons/text-style.svg?raw'
import brushSvg from '@/assets/icons/brush.svg?raw'
import imageSvg from '@/assets/icons/image.svg?raw'
import undoSvg from '@/assets/icons/undo.svg?raw'
import redoSvg from '@/assets/icons/redo.svg?raw'
import undoDisabledSvg from '@/assets/icons/undo-disabled.svg?raw'
import redoDisabledSvg from '@/assets/icons/redo-disabled.svg?raw'
import ulSvg from '@/assets/icons/ul.svg?raw'
import olSvg from '@/assets/icons/ol.svg?raw'

const ICONS = {
  add: addSvg,
  plus: addSvg,
  discover: discoverSvg,
  grid: discoverSvg,
  all: discoverSvg,
  article: articleSvg,
  list: articleSvg,
  uncategorized: articleSvg,
  calendar: calendarSvg,
  clock: calendarSvg,
  recent: calendarSvg,
  file: fileSvg,
  folder: fileSvg,
  stack: fileSvg,
  page: text1Svg,
  pages: text2Svg,
  edit: editSvg,
  pen: editSvg,
  share: shareSvg,
  'eye-on': eyeOnSvg,
  eye: eyeOnSvg,
  eye2: eyeOnSvg,
  'eye-off': eyeOffSvg,
  'menu-close': menuCloseSvg,
  menu: menuCloseSvg,
  'menu-open': menuOpenSvg,
  cloze: clozeSvg,
  sparkle: clozeSvg,
  chunk: chunkSvg,
  bold: boldSvg,
  strike: strikeSvg,
  underline: underlineSvg,
  italic: italicSvg,
  color: colorSvg,
  text: textStyleSvg,
  letter: textStyleSvg,
  'text-style': textStyleSvg,
  brush: brushSvg,
  image: imageSvg,
  undo: undoSvg,
  redo: redoSvg,
  'undo-disabled': undoDisabledSvg,
  'redo-disabled': redoDisabledSvg,
  ul: ulSvg,
  ol: olSvg
}

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 24 }
})

const resolved = computed(() => {
  const key = String(props.name || '')
  return ICONS[key] ? key : 'add'
})

function normalizeSvg(raw) {
  let s = String(raw)
  const m = s.match(/viewBox=["']([\d.-]+)\s+([\d.-]+)\s+([\d.]+)\s+([\d.]+)["']/)
  if (m) {
    const x = Number(m[1])
    const y = Number(m[2])
    const w = Number(m[3])
    const h = Number(m[4])
    if (x || y) {
      s = s.replace(/viewBox=["'][^"']+["']/, `viewBox="0 0 ${w} ${h}"`)
      s = s.replace(
        /(<svg\b[^>]*>)([\s\S]*)(<\/svg>)/,
        (_, open, inner, close) => `${open}<g transform="translate(${-x} ${-y})">${inner}</g>${close}`
      )
    }
  }
  return s.replace(/<svg\b/, '<svg overflow="hidden" width="100%" height="100%"')
}

const markup = computed(() => normalizeSvg(ICONS[resolved.value] || ICONS.add))

const boxStyle = computed(() => {
  const n = Number(props.size)
  const px = Number.isFinite(n) ? `${n}px` : String(props.size)
  return { width: px, height: px }
})
</script>

<style scoped>
.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  line-height: 0;
  color: inherit;
  overflow: hidden;
  pointer-events: none;
}

.app-icon :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
  overflow: hidden;
  pointer-events: none;
}
</style>
