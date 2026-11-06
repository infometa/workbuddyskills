<template>
  <div class="shell" :class="{ 'rail-off': railOff, editing: isEditing, batch: isBatch, 'brush-on': brushOn, 'ai-lock': aiLock }">

    <!-- Document View (Reading Mode) -->
    <div class="docview" :class="{ loading: isLoading }" ref="docViewRef">
      <header class="d-top">
        <div class="d-file">
          <button
            v-if="railOff"
            class="d-menu"
            type="button"
            aria-label="打开侧栏"
            @click="$emit('toggle-rail')"
          >
            <AppIcon class="ic" name="menu-open" :size="24" />
            菜单
          </button>
          <span v-if="railOff" class="d-menu-div" aria-hidden="true"></span>
          <button class="d-back" type="button" @click="goHome" aria-label="返回目录">
            <svg viewBox="0 0 24 24" width="20" height="20"><path d="m15 5-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <span class="fn">{{ docTitle }}</span>
          <span class="fm">{{ docMeta }}</span>
          <button class="d-toc" type="button" :class="{ on: tocVisible }" @click="toggleToc">目录</button>
        </div>
        <div class="d-acts">
          <button class="d-act primary" type="button" @click="openShare" v-show="false">
            <AppIcon name="share" :size="24" />
            分享
          </button>
          <button class="d-act" type="button" @click.stop="enterEdit()">
            <AppIcon class="ic" name="edit" :size="24" />
            编辑
          </button>
        </div>
      </header>

      <!-- Loading skeleton -->
      <div class="d-load" v-if="isLoading">
        <div class="d-load-inner">
          <div class="d-load-hd"><span class="d-spin"></span><span>正在打开资料…</span></div>
          <div class="skel h"></div>
          <div class="skel w1"></div>
          <div class="skel w2"></div>
          <div class="skel w3"></div>
          <div class="skel w4 gap"></div>
          <div class="skel h"></div>
          <div class="skel w1"></div>
          <div class="skel w2"></div>
          <div class="skel w3"></div>
          <div class="skel w2"></div>
          <div class="skel w4"></div>
        </div>
      </div>

      <!-- Document content -->
      <DynamicScroller
        :items="displayItems"
        :min-item-size="200"
        :buffer="2000"
        class="d-page"
        ref="dPageRef"
        @scroll="handlePageScroll"
      >
        <template v-slot="{ item, index, active }">
          <DynamicScrollerItem :item="item" :active="active" :size-dependencies="item.content">
            <div v-if="item.type === 'divider'" class="pagebreak">
              <span>第{{ item.page }}页</span>
            </div>
            <section
              v-else
              class="d-sec"
              :class="{ flipped: item.flipped, compact: item.compactFlip }"
              :style="item.flipped ? { minHeight: item.minHeight + 'px' } : {}"
              :data-qtitle="item.qtitle"
              :data-index="item.index"
              :data-chapter="item._chapterIdx"
              @mousedown="onSectionPointerDown"
              @click="toggleSectionFlip(item.index, $event)"
            >
            <div class="kb-front">
              <div class="kb-bar">
                <button
                  class="kb-ai"
                  type="button"
                  :class="{ busy: item.aiGenerating }"
                  :disabled="item.aiGenerating"
                  :aria-busy="item.aiGenerating"
                  @click.stop="genAiTitle(item.index)"
                >
                  <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.2 13.4 8.6 19 10l-5.6 1.4L12 16.8l-1.4-5.4L5 10l5.6-1.4z"/><path d="M18.6 14.2 19.45 16.7 22 17.55l-2.55.85-.85 2.5-.85-2.5-2.55-.85 2.55-.85z"/></svg>
                  {{ item.aiGenerating ? '生成中…' : 'AI生成标题' }}
                </button>
              </div>
              <div class="kb-mid">
                <div class="kb-title-wrap" :class="{ editing: item.editingTitle }">
                  <div
                    class="kb-q"
                    :class="{ generating: item.aiGenerating }"
                    :contenteditable="item.editingTitle && !item.aiGenerating"
                    @click="item.editingTitle && $event.stopPropagation()"
                    @beforeinput="onTitleBeforeInput"
                    @input="onTitleInput"
                    @paste="onTitlePaste"
                    @compositionend="onTitleInput"
                    @keydown.enter.prevent="endTitleEdit(item.index, true)"
                    @keydown.escape.prevent="endTitleEdit(item.index, false)"
                    @blur="endTitleEdit(item.index, true)"
                  >{{ clampBlockTitle(item.qtitle) }}</div>
                  <div class="kb-line"></div>
                </div>
                <span class="kb-edit-wrap" @click.stop>
                <button class="kb-edit" type="button" :class="{ on: item.editingTitle, locked: item.aiGenerating }" :aria-disabled="item.aiGenerating" @mousedown.prevent @click.stop="toggleTitleEdit(item.index)" aria-label="重命名">
                  <AppIcon class="ic" name="edit" :size="24" />
                </button>
                </span>
              </div>
              <div v-show="!item.compactFlip" class="kb-hint">点击查看原文</div>
            </div>
            <div class="kb-back" :ref="el => { if (el && (!el.__init || el.__content !== item.content)) { el.innerHTML = item.content; flattenNestedClozes(el); normalizeClozeDecorations(el); cleanupEmptyClozes(el); consolidateAllClozeGroups(el); hydrateReaderClozes(el); el.__content = item.content; el.__init = true } }"></div>
          </section>
          </DynamicScrollerItem>
        </template>
      </DynamicScroller>

      <button
        class="eye-fab"
        :class="{ revealed: allClozeRevealed }"
        type="button"
        @click="toggleAllCloze"
        :aria-label="allClozeRevealed ? '隐藏全部挖空' : '显示全部挖空'"
        :aria-pressed="allClozeRevealed"
      >
        <AppIcon class="eye-on" name="eye-on" :size="48" />
        <AppIcon class="eye-off" name="eye-off" :size="48" />
      </button>

      <!-- TOC Panel (在 docview 内, 不遮侧边栏) -->
      <div class="toc-panel" :class="{ on: tocVisible }">
        <div class="toc-head">
          <span class="toc-title">目录</span>
          <button class="toc-close" type="button" @click="closeToc">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="toc-body">
          <div
            v-for="ch in tocList"
            :key="ch.id"
            class="toc-item"
            :class="{ active: tocActiveId != null && String(ch.id) === String(tocActiveId) }"
            @click="jumpToChapter(ch.id)"
          >
            <svg class="toc-item-ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/></svg>
            <div class="toc-item-name">{{ ch.title }}</div>
          </div>
          <div class="toc-loading" v-if="tocLoading">
            <span class="toc-spin"></span><span>加载中…</span>
          </div>
          <div class="toc-nomore" v-if="!tocLoading && tocList.length > 0">
            — 已加载全部 —
          </div>
          <div class="toc-empty" v-if="!tocLoading && tocList.length === 0">
            暂无目录
          </div>
        </div>
      </div>
    </div>

  <!-- Edit View -->
    <div class="editview" ref="editViewRef">
      <header class="e-top">
        <button
          v-if="railOff"
          class="d-menu"
          type="button"
          aria-label="打开侧栏"
          @click="$emit('toggle-rail')"
        >
          <AppIcon class="ic" name="menu-open" :size="24" />
          菜单
        </button>
        <span v-if="railOff" class="d-menu-div" aria-hidden="true"></span>
        <button class="d-back" type="button" @click="requestLeaveEdit" aria-label="退出编辑">
          <svg viewBox="0 0 24 24" width="20" height="20"><path d="m15 5-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <span class="fn">编辑</span>
        <button class="d-toc" type="button" :class="{ on: tocVisible }" @click="toggleToc">目录</button>
        <div class="e-top-acts">
          <button class="d-act pill" :class="{ busy: aiBusy }" type="button" ref="aiClozeBtnRef" @click="openAiClozePick">
            <AppIcon class="ic" name="cloze" :size="24" />
            AI快速挖空
          </button>
          <button class="d-act pill" :class="{ busy: aiBusy }" type="button" @click="requestAiConfirm('chunk')">
            <AppIcon class="ic" name="chunk" :size="24" />
            AI快速分块
          </button>
          <button class="d-act primary" type="button" :disabled="saving" :class="{ busy: saving }" :aria-busy="saving" @click="doneEdit">
            <span v-if="saving" class="d-spin d-act-spin" aria-hidden="true"></span>
            完成
          </button>
        </div>
        <div class="e-batch-acts">
          <button class="d-act" type="button" @click="exitBatchMode">取消</button>
          <button v-if="batchMode === 'merge'" class="d-act merge" type="button" :disabled="pickedBlocks.length < 2" @click="mergeBlocks">合并（{{ pickedBlocks.length }}）</button>
          <button v-if="batchMode === 'delete'" class="d-act warn" type="button" :disabled="pickedBlocks.length < 1" @click="deleteBlocks">删除（{{ pickedBlocks.length }}）</button>
        </div>
      </header>

      <!-- TOC Panel (edit mode) -->
      <div class="toc-panel" :class="{ on: tocVisible }">
        <div class="toc-head">
          <span class="toc-title">目录</span>
          <button class="toc-close" type="button" @click="closeToc">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="toc-body">
          <div
            v-for="ch in tocList"
            :key="ch.id"
            class="toc-item"
            :class="{ active: tocActiveId != null && String(ch.id) === String(tocActiveId) }"
            @click="handleEditTocClick(ch.id)"
          >
            <svg class="toc-item-ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/></svg>
            <div class="toc-item-name">{{ ch.title }}</div>
          </div>
          <div class="toc-loading" v-if="tocLoading">
            <span class="toc-spin"></span><span>加载中…</span>
          </div>
          <div class="toc-nomore" v-if="!tocLoading && tocList.length > 0">
            — 已加载全部 —
          </div>
          <div class="toc-empty" v-if="!tocLoading && tocList.length === 0">
            暂无目录
          </div>
        </div>
      </div>

      <!-- Edit Toolbar -->
      <div class="etool" ref="editToolRef" @mousedown.prevent>
        <div class="etool-inner">
          <!-- Style -->
          <div class="etb etb-style" :class="{ open: etOpen.style }" data-et="style" @click="toggleEtool('style')">
            <AppIcon name="text" :size="24" />
            <span class="tx">{{ etStyleLabel }}</span>
            <svg class="chev" width="10" height="10" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <div class="etb-pop etb-style-pop" @click.stop>
              <div class="etb-opt" :class="{ cur: etStyle === 'p' }" data-et-style="p" @click="applyFormat('formatBlock', 'p')"><span class="si">T</span><span class="sn">正文</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></span></div>
              <div class="etb-opt" :class="{ cur: etStyle === 'h1' }" data-et-style="h1" @click="applyFormat('formatBlock', 'h1')"><span class="si">H1</span><span class="sn">一级标题</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></span></div>
              <div class="etb-opt" :class="{ cur: etStyle === 'h2' }" data-et-style="h2" @click="applyFormat('formatBlock', 'h2')"><span class="si">H2</span><span class="sn">二级标题</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></span></div>
              <div class="etb-opt" :class="{ cur: etStyle === 'h3' }" data-et-style="h3" @click="applyFormat('formatBlock', 'h3')"><span class="si">H3</span><span class="sn">三级标题</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></span></div>
            </div>
          </div>
          <span class="etool-div"></span>
          <div class="etb" :class="{ on: etStates.ol }" data-et="ol" title="有序列表" @click="applyFormat('insertOrderedList')"><AppIcon name="ol" :size="24" /><span class="tx">有序列表</span></div>
          <div class="etb" :class="{ on: etStates.ul }" data-et="ul" title="无序列表" @click="applyFormat('insertUnorderedList')"><AppIcon name="ul" :size="24" /><span class="tx">无序列表</span></div>
          <span class="etool-div"></span>
          <div class="etb" :class="{ on: etStates.bold }" data-et="bold" title="加粗" @click="applyFormat('bold')"><AppIcon name="bold" :size="24" /><span class="tx">加粗</span></div>
          <div class="etb" :class="{ on: etStates.italic }" data-et="italic" title="斜体" @click="applyFormat('italic')"><AppIcon name="italic" :size="24" /><span class="tx">斜体</span></div>
          <div class="etb" :class="{ on: etStates.underline }" data-et="underline" title="下划线" @click="applyFormat('underline')"><AppIcon name="underline" :size="24" /><span class="tx">下划线</span></div>
          <div class="etb" :class="{ on: etStates.strike }" data-et="strike" title="删除线" @click="applyFormat('strikeThrough')"><AppIcon name="strike" :size="24" /><span class="tx">删除线</span></div>
          <div class="etb" :class="{ open: etOpen.color }" data-et="color" title="颜色" @click="toggleEtool('color')">
            <AppIcon name="color" :size="24" /><span class="tx">颜色</span>
            <div class="etb-pop" @click.stop>
              <div class="etb-swatches">
                <i data-et-color="#222222" style="background:#222222" @click="applyFormat('foreColor', '#222222')"></i>
                <i data-et-color="#d24339" style="background:#d24339" @click="applyFormat('foreColor', '#d24339')"></i>
                <i data-et-color="#b5780a" style="background:#b5780a" @click="applyFormat('foreColor', '#b5780a')"></i>
                <i data-et-color="#1f9e6b" style="background:#1f9e6b" @click="applyFormat('foreColor', '#1f9e6b')"></i>
                <i data-et-color="#3e49c9" style="background:#3e49c9" @click="applyFormat('foreColor', '#3e49c9')"></i>
              </div>
            </div>
          </div>
          <span class="etool-div"></span>
          <div class="etb" :class="{ on: etStates.cloze }" data-et="cloze" title="挖空" @click="toggleCloze"><AppIcon name="cloze" :size="24" /><span class="tx">挖空</span></div>
          <div class="etb" :class="{ on: brushOn }" data-et="brush" title="挖空刷" @click="toggleBrush"><AppIcon name="brush" :size="24" /><span class="tx">挖空刷</span></div>
          <span class="etool-div"></span>
          <div class="etb" :class="{ on: isBatch, open: etOpen.block }" data-et="block" title="分块操作" @click="toggleEtool('block')">
            <AppIcon name="chunk" :size="24" />
            <span class="tx">分块操作</span>
            <svg class="chev" width="10" height="10" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="2"/></svg>
            <div class="etb-pop" @click.stop>
              <div class="etb-opt" @click="enterBatchMode('merge')">合并分块</div>
              <div class="etb-opt" @click="enterBatchMode('delete')">批量删除</div>
              <div class="etb-opt" @click="newBlock">新建分块</div>
              <div class="etb-opt" @click="splitBlock">分割分块</div>
            </div>
          </div>
          <div class="etb" title="插入图片" @click="pickImage">
            <AppIcon name="image" :size="24" /><span class="tx">插入图片</span>
          </div>
          <input ref="imageInputRef" class="etb-file" type="file" accept="image/*" @change="handleImagePicked" />
          <span class="etool-div"></span>
          <div class="etb" data-et="undo" title="撤销" :class="{ off: !canEditUndo }" @click="undo"><AppIcon :name="canEditUndo ? 'undo' : 'undo-disabled'" :size="24" /><span class="tx">撤销</span></div>
          <div class="etb" data-et="redo" title="重做" :class="{ off: !canEditRedo }" @click="redo"><AppIcon :name="canEditRedo ? 'redo' : 'redo-disabled'" :size="24" /><span class="tx">重做</span></div>
        </div>
      </div>

      <!-- Edit Content -->
      <div class="e-page" ref="ePageRef" @scroll="hideSelbar; closeMathEditor()">
        <div class="e-inner" ref="editBodyRef" id="editBody" @input="markDirty" @click="handleEditClick" @dblclick="onMathDblclick" @mousedown="handleEditMouseDown" @mouseup="handleEditMouseUp">
          <div
            v-for="(blk, i) in editBlocks"
            :key="blk.id"
            class="eblk"
            :class="{ picked: blk.picked, 'open-split': blk.splitOpen, 'drag-over': dragOverIdx === i }"
          >
            <label class="eblk-check">
              <input type="checkbox" v-model="blk.picked" @change="syncBatch" />
              <i><svg width="11" height="11" viewBox="0 0 12 12"><path d="M2 6.2 4.8 9 10 3.2" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></i>
            </label>
            <div class="eblk-side">
              <div class="eblk-handle" aria-hidden="true" @mousedown="onMouseDown(i, $event)">
                <svg width="16" height="16" viewBox="0 0 16 16" style="pointer-events:none"><circle cx="5" cy="3" r="1.3" fill="currentColor"/><circle cx="11" cy="3" r="1.3" fill="currentColor"/><circle cx="5" cy="8" r="1.3" fill="currentColor"/><circle cx="11" cy="8" r="1.3" fill="currentColor"/><circle cx="5" cy="13" r="1.3" fill="currentColor"/><circle cx="11" cy="13" r="1.3" fill="currentColor"/></svg>
              </div>
              <button v-if="!blk.isTable" class="eblk-split" type="button" @click="toggleSplit(i)">拆分</button>
              <div class="eblk-split-pop" role="menu">
                <button class="eblk-split-opt" type="button" @click="applyBlockSplit(i, 'line')">按行拆分</button>
                <button class="eblk-split-opt" type="button" @click="applyBlockSplit(i, 'blank')">按空白行拆分</button>
                <button class="eblk-split-opt" type="button" @click="applyBlockSplit(i, 'period')">按句号拆分</button>
              </div>
              <button class="eblk-del" type="button" @click.stop="deleteBlockAt(i)">删除</button>
            </div>
            <div
              v-if="!blk.isTable"
              class="eblk-txt"
              :contenteditable="!aiLock"
              :ref="el => { if (el) { console.log('[formula] ref block', i, 'isTable:', blk.isTable, 'htmlLen:', blk.html.length, 'hasMath:', blk.html.indexOf('class=&quot;math&quot;') > 0, 'init:', !!el.__init); if (!el.__init) { el.__init = true; nextTick(() => { el.innerHTML = prepareEditHtml(blk.html) }) }; editBlockRefs[i] = el } }"
              @input="onBlockInput(i, $event)"
              @beforeinput="onBlockBeforeInput"
              @keydown="handleEditKeydown"
              @mousedown="onEblkMouseDown"
            ></div>
            <div v-else class="eblk-txt vt">
              <div :id="'vtbl-' + blk.id" class="vt-host"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Cloze Pick -->
    <Teleport to="body">
      <div class="ai-cloze-pick" :class="{ on: czPickVisible }" :style="czPickStyle" ref="czPickRef">
        <button type="button" @click="openCzModal('ai')">AI挖空</button>
        <button type="button" @click="openCzModal('rule')">规则挖空</button>
        <button type="button" @click="openCzModal('tpl')">模版挖空</button>
      </div>
    </Teleport>

    <!-- AI overwrite confirm -->
    <Teleport to="body">
      <div class="ai-confirm" :class="{ on: aiConfirm.visible }" :aria-hidden="!aiConfirm.visible">
        <div class="ai-confirm-scrim" @click="cancelAiConfirm"></div>
        <div class="ai-confirm-card" role="dialog" aria-modal="true" aria-labelledby="aiConfirmTitle">
          <p class="ai-confirm-txt" id="aiConfirmTitle">{{ aiConfirmText }}</p>
          <div class="ai-confirm-acts">
            <button class="ai-confirm-cancel" type="button" @click="cancelAiConfirm">取消</button>
            <button class="ai-confirm-ok" type="button" @click="confirmAiAction">确认</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Cloze Bubble -->
    <Teleport to="body">
      <div class="cloze-bubble" :class="{ on: clozeBubbleVisible, below: clozeBubbleBelow }" :style="clozeBubbleStyle" role="toolbar" aria-label="挖空">
        <button type="button" @click="applyReadCloze">挖空</button>
      </div>
    </Teleport>

    <!-- Selection Toolbar -->
    <Teleport to="body">
      <div class="selbar" :class="{ on: selbarVisible, below: selbarBelow }" :style="selbarStyle" role="toolbar" aria-label="文本工具" ref="selbarRef" @mousedown.prevent="rememberToolbarRange">
        <div class="selbar-item" :class="{ open: selOpen.style }" data-act="style" @click="toggleSelPopup('style')">
          <AppIcon name="text" :size="24" /><span class="lb">样式</span>
          <div class="selbar-pop style-drawer" @click.stop>
            <div class="selbar-opt" :class="{ cur: selStyle === 'p' }" data-style="p" @click="applySelStyle('p')"><span class="si">T</span><span class="sn">正文</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2"/></svg></span></div>
            <div class="selbar-opt" :class="{ cur: selStyle === 'h1' }" data-style="h1" @click="applySelStyle('h1')"><span class="si">H1</span><span class="sn">一级标题</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2"/></svg></span></div>
            <div class="selbar-opt" :class="{ cur: selStyle === 'h2' }" data-style="h2" @click="applySelStyle('h2')"><span class="si">H2</span><span class="sn">二级标题</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2"/></svg></span></div>
            <div class="selbar-opt" :class="{ cur: selStyle === 'h3' }" data-style="h3" @click="applySelStyle('h3')"><span class="si">H3</span><span class="sn">三级标题</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2"/></svg></span></div>
            <div class="selbar-opt" :class="{ cur: selStyle === 'ol' }" data-style="ol" @click="applySelStyle('ol')"><span class="si"><AppIcon name="ol" :size="24" /></span><span class="sn">有序列表</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2"/></svg></span></div>
            <div class="selbar-opt" :class="{ cur: selStyle === 'ul' }" data-style="ul" @click="applySelStyle('ul')"><span class="si"><AppIcon name="ul" :size="24" /></span><span class="sn">无序列表</span><span class="sk"><svg width="16" height="16" viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.2"/></svg></span></div>
          </div>
        </div>
        <span class="selbar-div"></span>
        <div class="selbar-item" :class="{ on: selStates.bold }" data-act="bold" @mousedown.prevent="applySelCmd('bold')"><AppIcon name="bold" :size="24" /><span class="lb">加粗</span></div>
        <div class="selbar-item" :class="{ on: selStates.italic }" data-act="italic" @mousedown.prevent="applySelCmd('italic')"><AppIcon name="italic" :size="24" /><span class="lb">斜体</span></div>
        <div class="selbar-item" :class="{ on: selStates.underline }" data-act="underline" @mousedown.prevent="applySelCmd('underline')"><AppIcon name="underline" :size="24" /><span class="lb">下划线</span></div>
        <div class="selbar-item" :class="{ on: selStates.strike }" data-act="strike" @mousedown.prevent="applySelCmd('strikeThrough')"><AppIcon name="strike" :size="24" /><span class="lb">删除线</span></div>
        <div class="selbar-item" :class="{ open: selOpen.color }" data-act="color" @click="toggleSelPopup('color')">
          <AppIcon name="color" :size="24" /><span class="lb">颜色</span>
          <div class="selbar-pop" @click.stop>
            <div class="selbar-swatches">
              <i data-color="#222222" style="background:#222222" @click="applySelColor('#222222')"></i>
              <i data-color="#d24339" style="background:#d24339" @click="applySelColor('#d24339')"></i>
              <i data-color="#b5780a" style="background:#b5780a" @click="applySelColor('#b5780a')"></i>
              <i data-color="#1f9e6b" style="background:#1f9e6b" @click="applySelColor('#1f9e6b')"></i>
              <i data-color="#3e49c9" style="background:#3e49c9" @click="applySelColor('#3e49c9')"></i>
            </div>
          </div>
        </div>
        <span class="selbar-div"></span>
        <div class="selbar-item cloze-act" :class="{ on: selInCloze }" data-act="cloze" @mousedown.prevent="applySelCloze">
          <AppIcon name="cloze" :size="24" /><span class="lb">挖空</span>
        </div>
      </div>
    </Teleport>

    <!-- Math Editor -->
    <Teleport to="body">
      <div v-if="mathEdit.visible" class="me-mask" @mousedown="closeMathEditor" @contextmenu.prevent></div>
      <div v-if="mathEdit.visible" class="math-editor" :style="mathEditStyle" role="dialog" aria-label="编辑公式">
        <div class="me-head">
          <span>编辑公式</span>
          <code class="me-delim">$$ ... $$</code>
        </div>
        <div class="me-toolbar" @mousedown="e => e.preventDefault()">
          <button class="me-tb-btn" title="分数 \frac{a}{b}" @click="insertMathTpl('\\frac{}{}')"><span class="me-tb-frac"><i>a</i><i>b</i></span></button>
          <button class="me-tb-btn" title="平方 \sqrt{x}" @click="insertMathTpl('\\sqrt{}')">√</button>
          <button class="me-tb-btn" title="求和 ∑" @click="insertMathTpl('\\sum_{}^{}')">∑</button>
          <button class="me-tb-btn" title="积分 ∫" @click="insertMathTpl('\\int_{}^{}')">∫</button>
          <button class="me-tb-btn" title="乘积 ∏" @click="insertMathTpl('\\prod_{}^{}')">∏</button>
          <button class="me-tb-btn" title="极限 lim" @click="insertMathTpl('\\lim_{}')">lim</button>
          <span class="me-tb-split"></span>
          <button class="me-tb-btn" title="α" @click="insertMathTpl('\\alpha')">α</button>
          <button class="me-tb-btn" title="β" @click="insertMathTpl('\\beta')">β</button>
          <button class="me-tb-btn" title="γ" @click="insertMathTpl('\\gamma')">γ</button>
          <button class="me-tb-btn" title="θ" @click="insertMathTpl('\\theta')">θ</button>
          <button class="me-tb-btn" title="π" @click="insertMathTpl('\\pi')">π</button>
          <button class="me-tb-btn" title="σ" @click="insertMathTpl('\\sigma')">σ</button>
          <button class="me-tb-btn" title="ω" @click="insertMathTpl('\\omega')">ω</button>
          <button class="me-tb-btn" title="Δ" @click="insertMathTpl('\\Delta')">Δ</button>
          <span class="me-tb-split"></span>
          <button class="me-tb-btn" title="≠" @click="insertMathTpl('\\neq')">≠</button>
          <button class="me-tb-btn" title="≈" @click="insertMathTpl('\\approx')">≈</button>
          <button class="me-tb-btn" title="≤" @click="insertMathTpl('\\leq')">≤</button>
          <button class="me-tb-btn" title="≥" @click="insertMathTpl('\\geq')">≥</button>
          <button class="me-tb-btn" title="×" @click="insertMathTpl('\\times')">×</button>
          <button class="me-tb-btn" title="÷" @click="insertMathTpl('\\div')">÷</button>
          <span class="me-tb-split"></span>
          <button class="me-tb-btn" title="∞" @click="insertMathTpl('\\infty')">∞</button>
          <button class="me-tb-btn" title="偏导 ∂" @click="insertMathTpl('\\partial')">∂</button>
          <button class="me-tb-btn" title="∇" @click="insertMathTpl('\\nabla')">∇</button>
          <button class="me-tb-btn" title="上标 ^{}" @click="insertMathTpl('^{}')"><sup>x</sup></button>
          <button class="me-tb-btn" title="下标 _{}" @click="insertMathTpl('_{}')"><sub>x</sub></button>
          <button class="me-tb-btn" title="括号 ()" @click="insertMathTpl('()')">( )</button>
          <button class="me-tb-btn" title="绝对值 |x|" @click="insertMathTpl('||')">| |</button>
        </div>
        <textarea
          ref="mathInputRef"
          v-model="mathEdit.value"
          class="me-input"
          rows="3"
          spellcheck="false"
          placeholder="输入 LaTeX 源码，如 \sqrt{\frac{a}{b}} 或 \begin{matrix}1&amp;2\\3&amp;4\end{matrix}"
          @keydown="onMathEditorKeydown"
          @input="readMathPreview"
        ></textarea>
        <div v-show="mathEdit.value.trim()" class="me-preview" :class="{ err: !!mathEditError }">
          <span v-if="mathEditError" class="me-err">{{ mathEditError }}</span>
          <span v-else v-html="mathEditPreview"></span>
        </div>
        <div class="me-btns">
          <button type="button" class="me-btn" @click="closeMathEditor">取消</button>
          <button type="button" class="me-btn primary" @click="applyMathEdit">应用</button>
        </div>
      </div>
    </Teleport>
  <!-- CzModal -->
    <CzModal
      :visible="czModalVisible"
      :kind="czState.kind"
      @close="czModalVisible = false"
      @run="handleCzRun"
      @flash="flash"
    />

    <!-- AiMask -->
    <AiMask
      :visible="aiMaskVisible"
      :text="aiMaskText"
      :duration="AI_JOB_MS"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { bookApi } from '@/utils/api'
import MarkdownIt from 'markdown-it'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import CzModal from '../components/CzModal.vue'
import AiMask from '../components/AiMask.vue'
import AppIcon from '../components/AppIcon.vue'

// markdown-it 渲染器：html:true 透传 txt 里已有的内联 HTML（如 <br>），table/标题/列表等按原格式渲染
const md = new MarkdownIt({ html: true })

// $$...$$ / $...$ LaTeX 公式：注册在 text 规则之前，整段捕获源码 token，
// 使 \[、\_ 等 LaTeX 反斜杠不被 markdown-it 的转义规则提前吞掉。
// 用正则匹配，guard 与 renderMathInRichText 规则一致：
//   单 $ 开符后不能是空白/数字/$，闭符前不能是空白/$，闭符后不能是数字（价格 $5 不算公式）
function mathInline(state, silent) {
  const src = state.src
  const start = state.pos
  if (src.charCodeAt(start) !== 0x24) return false
  // \$ 转义过的美元符不算公式
  if (start > 0 && src[start - 1] === '\\') return false
  const rest = src.slice(start)
  let m, tex, isDouble, end
  if (rest.startsWith('$$')) {
    // 双美元 $$...$$：内容可为空（含换行视为块级公式）
    m = rest.match(/^\$\$([\s\S]*?)\$\$/)
    if (!m) return false
    tex = m[1].trim()
    if (!tex) return false
    isDouble = true
    end = start + m[0].length
  } else {
    // 单美元 $...$：正则 guard + 内容须含 LaTeX 特征（\ ^ _ { }）或为单字母变量
	    // 允许数字开头（如 $0.8 \div 5.7$），数字纯文本（如 $5）由后续 guard 过滤
    m = rest.match(/^\$([^\s$][^\n$]*)(?<!\s)\$(?!\d)/)
    if (!m) return false
    tex = m[1]
    if (!tex || (!/[\\^_{}]/.test(tex) && !/^[a-zA-Z]$/.test(tex))) return false
    isDouble = false
    end = start + m[0].length
  }
  state.pos = end
  if (silent) return true
  const token = state.push('math_inline', 'math', 0)
  token.content = tex
  token.markup = isDouble ? '$$' : '$'
  return true
}
md.inline.ruler.before('text', 'math_inline', mathInline)

// data-math 属性转义：保存时用它还原 $$源码$$，属性里的引号等需转义
const escAttr = s => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// 公式展示统一用 <span class="math">（不落库：保存时仍还原为 $...$）。
// class/data-math 协议保持不变，双击编辑、表格序列化、保存还原全部复用 .
md.renderer.rules.math_inline = (tokens, idx) => {
  const tex = tokens[idx].content
  // 单行内的 $$...$$ 按行内公式渲染；内容含换行视为块级公式
  const html = katex.renderToString(tex, { displayMode: tex.includes('\n'), throwOnError: false, strict: false })
  return `<span class="math" data-math="${escAttr(tex)}" title="${escAttr(tex)}">${html}</span>`
}

// TXT 富文本(richTxt)里的 $$...$$ / $...$ 公式：按标签切分，只在文本段内渲染，
// 标签属性里的 $$（如 title="100$$x$$"）不会被误处理；已渲染过的 .math 元素原样保留（幂等）。
// 单 $ 的 guard 与 MathInline 规则一致：开符后/闭符前紧邻空白、数字、$ 的不算公式（价格 $5）
function renderMathInRichText(html) {
  if (!html || !html.includes('$')) return html
  return html.split(/(<[^>]*>)/g).map(part => {
    if (part.startsWith('<')) return part
    return part
      // 双美元优先（内容可含换行，块级公式）
      .replace(/\$\$([\s\S]*?)\$\$/g, (m, tex) => {
        tex = tex.trim()
        if (!tex || tex.includes('<') || tex.includes('>')) return m
        const html = katex.renderToString(tex, { displayMode: tex.includes('\n'), throwOnError: false, strict: false })
        return `<span class="math" data-math="${escAttr(tex)}" title="${escAttr(tex)}">${html}</span>`
      })
      // 单美元：行内公式，内容不含换行与 $；闭符前非空白，闭符后非数字（$x$5 按文本）
      .replace(/\$([^\s$][^\n$]*)(?<!\s)\$(?!\d)/g, (m, tex) => {
        if (tex.includes('<') || tex.includes('>')) return m
        if (!/[\\^_{}]/.test(tex) && !/^[a-zA-Z]$/.test(tex)) return m
        const html = katex.renderToString(tex, { displayMode: false, throwOnError: false, strict: false })
        return `<span class="math" data-math="${escAttr(tex)}" title="${escAttr(tex)}">${html}</span>`
      })
  }).join('')
}

// 保存时把 .math 的 data-math 源码还原为 $...$ 文本，不把 KaTeX 渲染 HTML 落进 richTxt/txt。
// 统一还原为单美元：vditor(Lute) 原生只认 $...$（$$ 在其引擎里渲染错乱），渲染层单双都兼容、
// 旧 $$ 数据加载展示不受影响，保存一次后收敛为单美元
function restoreMathSpans(root) {
  root.querySelectorAll('.math').forEach(sp => {
    const tex = sp.getAttribute('data-math') || ''
    sp.replaceWith(document.createTextNode(`$${tex}$`))
  })
}

const props = defineProps({
  categories: { type: Array, required: true },
  folderGroups: { type: Array, required: true },
  homeCat: { type: String, default: '全部' },
  currentDoc: { type: String, default: null },
  railOff: { type: Boolean, default: false },
  doc: { type: Object, default: null },
  isNewDoc: { type: Boolean, default: false },
  autoEdit: { type: Boolean, default: false }
})

const emit = defineEmits([
  'open-add', 'open-dlapp', 'toggle-rail', 'row-action', 'flash', 'go-home',
  'open-share', 'open-feedback', 'open-unsaved', 'save-doc', 'save-book',
  'edit-entered'
])

// Document state
const isLoading = ref(true)
const docViewRef = ref(null)
const dPageRef = ref(null)
const scrollEl = computed(() => dPageRef.value?.$el || null)
const sections = ref([])
const allClozeRevealed = ref(true)
let clozeRevealByText = new Map()

// 主内容分页 & 逐章加载
const chapterList = ref([])         // 章节列表，每项包含 { id, title, _content(加载后填充), ... }

// 从 chapterList 重建 sections 数组（只包含已加载的章节，未加载的排除）
function rebuildSections() {
  const allItems = []
  for (let i = 0; i < chapterList.value.length; i++) {
    const ch = chapterList.value[i]
    if (ch._content) {
      // 给每个 item 标记实际章节索引，用于页码显示
      ch._content.forEach((item, j) => {
        // 没有后端 id 的块用「章序号-章内序号」兜底：重建后 key 保持稳定，
        // 虚拟列表才能复用已测量的尺寸，避免每次插入章节都整表重新测量导致错位
        allItems.push({ ...item, _chapterIdx: i, id: item.id ?? `sec-${i}-${j}` })
      })
    }
  }
  sections.value = allItems
}

// 获取下一个未加载的章节索引（从已加载的最后一张往后找）
function getNextUnloadedChapter() {
  let lastLoaded = -1
  let firstLoaded = chapterList.value.length
  for (let i = 0; i < chapterList.value.length; i++) {
    if (chapterList.value[i]._content) {
      lastLoaded = i
      if (i < firstLoaded) firstLoaded = i
    }
  }
  // 优先加载最后已加载章节之后的章节
  for (let i = lastLoaded + 1; i < chapterList.value.length; i++) {
    if (!chapterList.value[i]._content) return i
  }
  // 只补齐已加载区间内部的空缺。不从头环绕加载：
  // 目录跳到末尾后身处底部时，更早的章节应交给向上滚动 + loadPrevChapter（带滚动补偿），
  // 否则内容前插会造成阅读位置错乱，中间章节无法正常阅读。
  for (let i = firstLoaded; i <= lastLoaded; i++) {
    if (!chapterList.value[i]._content) return i
  }
  return -1
}

// 展平列表：章节间显示分割线，块之间不显示
const displayItems = computed(() => {
  const items = []
  let afterTitle = false
  let prevChapterIdx = -1
  for (let origIdx = 0; origIdx < sections.value.length; origIdx++) {
    const s = sections.value[origIdx]
    if (s.type === 'chapterTitle') {
      afterTitle = true
      continue
    }
    // 新章节的第一个块前显示分割线（从第2章开始），页码用实际章节索引
    if (afterTitle && prevChapterIdx >= 0) {
      items.push({ type: 'divider', page: chapterList.value[prevChapterIdx]?.pageNumber ?? prevChapterIdx + 1, id: 'div-' + prevChapterIdx })
    }
    afterTitle = false
    prevChapterIdx = s._chapterIdx
    items.push({ type: 'section', index: origIdx, id: s.id || 'sec-' + origIdx, ...s })
  }
  return items
})

// 目录跳转期间暂停自动加载，避免落地在底部/顶部时触发前后章加载干扰定位
let isChapterJumping = false
let chapterJumpSeq = 0

// 预加载窗口：前进方向只补「可见页之后 5 页」内的空缺（向前查缺、逐页补载，不整批拉 5 页）
const LOOKAHEAD_CHAPTERS = 5
let lastReaderScrollTop = 0

// 当前视口顶部第一个内容块所属的章节索引：已渲染 DOM 里第一个越过视口顶线的块；
// 取不到（如尚未渲染任何块）返回 -1
function getVisibleChapter() {
  const el = scrollEl.value
  if (!el) return -1
  const scrollerTop = el.getBoundingClientRect().top
  for (const sec of el.querySelectorAll('.d-sec[data-chapter]')) {
    // 顶部以上的块整块 bottom 都在顶线之上；有任意部分低于顶线即当前可见页
    if (sec.getBoundingClientRect().bottom > scrollerTop + 1) {
      return Number(sec.dataset.chapter)
    }
  }
  return -1
}

function handlePageScroll() {
  const el = scrollEl.value
  if (!el) return
  scheduleSaveReaderPos()
  if (isChapterJumping) return
  if (!sections.value.length) return

  const scrollTop = el.scrollTop
  const direction = scrollTop - lastReaderScrollTop
  lastReaderScrollTop = scrollTop

  const visibleChapter = getVisibleChapter()
  if (visibleChapter < 0) return

  // 前进（下滚）：向前查 5 章窗口有缺口就补（另一方向的补载进行中时跳过，
  // 保证同一时刻只有一条章节请求在飞）
  if (direction >= 0 && !loadingPrev && getLoadAheadTarget() >= 0) {
    hideClozeBubble()
    loadNextChapter()
  }
  // 回翻（往上翻）：往前查 5 章窗口有缺口就补
  if (direction <= 0 && !loadingNext && getPrevUnloadedChapter() >= 0) {
    loadPrevChapter()
  }
}

const READER_POS_KEY = 'bsj.readerPos'
let readerPosReady = false
let readerPosTimer = null

function readReaderPosMap() {
  try {
    const raw = sessionStorage.getItem(READER_POS_KEY)
    if (!raw) return {}
    const data = JSON.parse(raw)
    return data && typeof data === 'object' ? data : {}
  } catch {
    return {}
  }
}

function scheduleSaveReaderPos() {
  if (!readerPosReady || isEditing.value) return
  clearTimeout(readerPosTimer)
  readerPosTimer = setTimeout(saveReaderPos, 200)
}

function saveReaderPos() {
  if (!readerPosReady) return
  const bookId = props.currentDoc
  const el = scrollEl.value
  if (!bookId || !el || String(bookId).startsWith('added')) return
  try {
    const all = readReaderPosMap()
    // 计算已加载的最大章节索引
    let maxLoaded = -1
    for (let i = 0; i < chapterList.value.length; i++) {
      if (chapterList.value[i]._content) maxLoaded = i
    }
    all[bookId] = {
      scrollTop: Math.max(0, Math.round(el.scrollTop)),
      loadedChapters: maxLoaded + 1 // 兼容旧格式
    }
    sessionStorage.setItem(READER_POS_KEY, JSON.stringify(all))
  } catch { /* ignore quota / private mode */ }
}

async function restoreReaderPos(bookId) {
  const saved = readReaderPosMap()[bookId]
  if (!saved || !(saved.scrollTop > 8)) {
    readerPosReady = true
    return
  }
  const targetChapters = Math.max(1, saved.loadedChapters || 1)
  // 加载目标章节前后章节（不再逐个加载前面的所有章节）
  const start = Math.max(0, targetChapters - 2)
  const end = Math.min(chapterList.value.length - 1, targetChapters + 1)
  for (let i = start; i <= end; i++) {
    if (!chapterList.value[i]?._content) {
      await loadChapter(i)
    }
  }
  rebuildSections()
  await nextTick()
  const el = scrollEl.value
  if (el) {
    let guard = 0
    while (el.scrollHeight < saved.scrollTop + el.clientHeight && guard < 40) {
      const prevH = el.scrollHeight
      const nextIdx = getNextUnloadedChapter()
      if (nextIdx >= 0) {
        await loadChapter(nextIdx)
        rebuildSections()
      } else {
        break
      }
      await nextTick()
      if (el.scrollHeight === prevH) break
      guard++
    }
    el.scrollTop = saved.scrollTop
  }
  readerPosReady = true
}

// IMG 块本地上传缓存：objId → dataURL（保存后重载时用于展示；刷新后需后端提供图片 URL）
const imgObjCache = new Map()

// 把内嵌 dataURL 图片上传，返回 ResourceDataBean（objId/objKey）
async function uploadImageDataUrl(dataUrl) {
  const blob = await (await fetch(dataUrl)).blob()
  const ext = blob.type === 'image/png' ? 'png' : blob.type === 'image/gif' ? 'gif' : blob.type === 'image/jpeg' ? 'jpg' : 'png'
  const file = new File([blob], `image-${Date.now()}.${ext}`, { type: blob.type })
  const res = await bookApi.uploadImg(file)
  if (res.code !== 0 || !Array.isArray(res.data) || !res.data[0]) {
    throw new Error(res.msg || '图片上传失败')
  }
  const bean = res.data[0]
  imgObjCache.set(bean.objId, dataUrl)
  return bean
}

// 渲染 markdown 内容（TABLE 块等）；空值返回空串
function renderMarkdownBlock(markdownText) {
  const text = String(markdownText || '').trim()
  return text ? md.render(text) : ''
}

// 生成章节块的展示内容：IMG 块用本地缓存图片，TABLE 块用 markdown-it 渲染 txt，TXT 块用 richTxt/txt
function buildBlockContent(blk) {
  const bean = blk.dataBaseBean || {}
  if (bean.importedRecitationPage) return bean.richTxt || ''
  if (bean.bookDataType === 'IMG') {
    const objId = bean.resourceDataBean && bean.resourceDataBean.objId
    const local = objId && imgObjCache.get(objId)
    if (local) return `<figure class="blk-img"><img src="${local}" alt="" /></figure>`
    return ''
  }
  if (bean.bookDataType === 'TABLE') {
    const rendered = renderMarkdownBlock(bean.txt)
    if (rendered) return `<div class="md-block">${rendered}</div>`
    return renderMathInRichText(bean.richTxt || '')
  }
  // TXT 块：渲染富文本前先处理其中的 $$...$$ 公式
  return renderMathInRichText(bean.richTxt || (bean.txt ? `<html><body>${bean.txt}</body></html>` : ''))
}

// 把编辑后的 <table> 序列化回 markdown 管道表格：TABLE 块保存时 txt 字段保持 markdown 格式
function tableToMarkdown(tableEl) {
  const rows = Array.from(tableEl.rows)
  if (!rows.length) return ''
  // 单元格 HTML → 单行文本：contenteditable 产生的块级标签收敛为 <br>，空白折叠，
  // 特殊标点补反斜杠转义（还原后端 \[、\( 之类写法），| 转义防破坏表格结构
  const cellText = cell => {
    const clone = cell.cloneNode(true)
    // KaTeX 渲染后的公式：源码从 data-math 取回并先提取为占位符，避开通用标点转义 ——
    // LaTeX 的 \{、\[ 与 {、[ 语义不同，不能改写；仅 | 需转义以保表格结构
    const mathParts = []
    clone.querySelectorAll('.math').forEach(sp => {
      const tex = sp.getAttribute('data-math') || ''
      mathParts.push(`$${tex.replace(/\|/g, '\\|')}$`)
      sp.replaceWith(document.createTextNode(`MATHHOLDER${mathParts.length - 1}MATHHOLDER`))
    })
    let html = (clone.innerHTML || '')
      .replace(/<(p|div)(?:\s[^>]*)?>/gi, '')
      .replace(/<\/(p|div)>/gi, '<br>')
      .replace(/&nbsp;/g, ' ')
      .replace(/\s+/g, ' ')
      .replace(/<br\s*\/?>/gi, '<br>')
      .replace(/(<br>)+/g, '<br>')
      .trim()
      .replace(/^(<br>)+|(<br>)+$/g, '')
    // 单元格里未渲染的 $$公式$$ / $公式$ 文本段（无 .math 元素，如直接粘贴的源码）同样提为占位符，
    // 否则 ( + 等会被标点转义写成 \(1\+i\)，公式语义被破坏。guard 与渲染规则一致（价格 $5 不算公式）
    html = html.replace(/\$\$([\s\S]*?)\$\$|\$[^\s$0-9][^\n$]*(?<!\s)\$(?!\d)/g, m => {
      if (m.startsWith('$$') || /[\\^_{}]/.test(m.slice(1, -1)) || /^[a-zA-Z]$/.test(m.slice(1, -1))) {
        mathParts.push(m)
        return `MATHHOLDER${mathParts.length - 1}MATHHOLDER`
      }
      return m
    })
    // 特殊标点补反斜杠转义（还原后端 \[、\( 之类写法，| 转义防破坏表格结构）。
    // (?<!\\) 负向后视保证幂等：已经是 \x 转义序列的标点不再重复转义，
    // 否则 (EOQ) → \(EOQ\) → \\(EOQ\\)，每次保存 \ 层层叠加、重载后就显示多余反斜杠
    html = html.replace(/(?<!\\)([`*_{}\[\]()#+.\-!|])/g, '\\$1')
    // 公式段回填：原样源码，避免 \[、\{ 被转义后 KaTeX 解析失败
    // 注意用函数替换（而非模板串）：$$ 在置换串里会被当成单个 $ 的转义
    mathParts.forEach((m, i) => { html = html.replaceAll(`MATHHOLDER${i}MATHHOLDER`, () => m) })
    return html
  }
  // 还原 markdown-it 渲染时写入单元格的对齐样式，分隔行用 :--- / ---: / :---: 表达
  const alignOf = cell => {
    const m = /text-align\s*:\s*(left|center|right)/i.exec(cell.getAttribute('style') || '')
    return m ? m[1] : null
  }
  const sepCell = a => (a === 'left' ? ':---' : a === 'center' ? ':---:' : a === 'right' ? '---:' : '---')
  const line = cells => `| ${cells.map(cellText).join(' | ')} |`

  // 有 thead 则用它做表头行；无表头时用第一行做表头并生成分隔行，保证 markdown-it 重新渲染时仍按表格解析
  const thead = tableEl.querySelector('thead')
  const headerRow = thead ? thead.rows[0] : null
  const headerCells = headerRow ? Array.from(headerRow.cells) : rows.length ? Array.from(rows[0].cells) : []
  const bodyRows = headerRow ? rows.filter(r => r !== headerRow) : rows.slice(1)
  const lines = [
    line(headerCells),
    `| ${headerCells.map(c => sepCell(alignOf(c))).join(' | ')} |`
  ]
  bodyRows.forEach(r => lines.push(line(Array.from(r.cells))))
  return lines.join('\n')
}

// 把后端返回的章节块编译为展示项；IMG 块无本地缓存时调用 objKey 转 URL 接口补图
async function compileChapterItems(bookDataList, chapterId, chapterTitle) {
  const items = [{ type: 'chapterTitle', text: chapterTitle, chapterId }]
  const pending = []   // { itemsIndex, objId, objKey }
  bookDataList.forEach((blk, i) => {
    const content = buildBlockContent(blk)
    const bean = blk.dataBaseBean || {}
    const isTable = bean.bookDataType === 'TABLE'
    items.push({
      id: blk.id,
      qtitle: clampBlockTitle(blk.title || `章节 ${i + 1}`),
      content,
      chapterId,
      pageNumber: blk.pageNumber,
      flipped: false,
      minHeight: 0,
      editingTitle: false,
      aiGenerated: false,
      aiGenerating: false,
      compactFlip: false,
      isTable,
      txt: isTable ? (blk.txt ?? bean.txt ?? '') : ''
    })
    const res = bean.resourceDataBean
    if (bean.bookDataType === 'IMG' && res && !content) {
      pending.push({ itemsIndex: items.length - 1, objId: res.objId, objKey: res.objKey })
    }
  })
  if (pending.length) {
    const urls = await Promise.all(pending.map(w =>
      bookApi.objToUrl(w.objKey).then(r => (r.code === 0 ? r.data : null)).catch(() => null)
    ))
    pending.forEach((w, i) => {
      if (urls[i]) {
        imgObjCache.set(w.objId, urls[i])
        items[w.itemsIndex].content = `<figure class="blk-img"><img src="${urls[i]}" alt="" /></figure>`
      }
    })
  }
  return items
}

// 加载指定索引的章节（支持任意跳转，自动缓存）
const chapterLoading = new Map() // idx → Promise，防重复请求

async function loadChapter(idx) {
  if (idx < 0 || idx >= chapterList.value.length) return false
  if (chapterList.value[idx]._content) return true
  if (chapterLoading.has(idx)) {
    return chapterLoading.get(idx)
  }
  const promise = loadChapterInternal(idx)
  chapterLoading.set(idx, promise)
  return promise
}

async function loadChapterInternal(idx) {
  const ch = chapterList.value[idx]
  try {
    const detail = await bookApi.getDetail({ id: ch.id })
    if (detail.code === 0 && detail.data && Array.isArray(detail.data.bookDataList)) {
      const chapterTitle = ch.title || `第 ${idx + 1} 章`
      const newItems = await compileChapterItems(detail.data.bookDataList, ch.id, chapterTitle)
      ch._content = newItems
      // 不在这里调 rebuildSections，由调用方批量加载完后统一调一次
      return true
      return true
    }
    console.warn('[loadChapterInternal] API返回数据异常, idx:', idx, 'code:', detail.code)
  } catch (err) {
    console.warn('[loadChapterInternal] 加载章节失败, idx:', idx, err)
  } finally {
    chapterLoading.delete(idx)
  }
  return false
}

// 顺序加载下一章（向前查 5 章窗口：每次只发一个请求，加载完自动查下一章，逐条往前直到窗口填满）
const PRELOAD_STEP_DELAY = 400 // 相邻两次预载之间的间隔：网络面板里一次只有一条请求在飞
let loadingNext = false
async function loadNextChapter() {
  if (loadingNext) return
  loadingNext = true
  try {
    await loadNextChapterInternal()
  } finally {
    loadingNext = false
  }
}

async function loadNextChapterInternal() {
  // 查缺循环：每次加载窗口内第一个未加载章节，稍作停顿再查下一个
  for (let guard = 0; guard < LOOKAHEAD_CHAPTERS + 2; guard++) {
    const idx = getLoadAheadTarget()
    if (idx < 0) return
    console.log('[loadNextChapter] 预载未加载章节 idx:', idx)
    const success = await loadChapter(idx)
    if (!success) return
    rebuildSections()
    // 停一下再往前走：请求逐条发出，不会连成一片
    await new Promise(r => setTimeout(r, PRELOAD_STEP_DELAY))
  }
}

// 向前查「预载窗口内」第一个未加载的章节；窗口内都已加载返回 -1。
// 窗口 = 当前可见页之后的 5 页；可见页取不到时（首次加载、尚未渲染），
// 退化为「已加载尾部 + 5 章」封顶，避免把整本书逐章载完
function getLoadAheadTarget() {
  let firstLoaded = chapterList.value.length
  let lastLoaded = -1
  for (let i = 0; i < chapterList.value.length; i++) {
    if (chapterList.value[i]._content) {
      if (i < firstLoaded) firstLoaded = i
      lastLoaded = i
    }
  }
  const visibleChapter = getVisibleChapter()
  const horizon = Math.min(
    chapterList.value.length - 1,
    visibleChapter < 0 ? lastLoaded + LOOKAHEAD_CHAPTERS : visibleChapter + LOOKAHEAD_CHAPTERS
  )
  // 从已加载尾部往后，找窗口内第一个空缺
  for (let i = lastLoaded + 1; i <= horizon; i++) {
    if (!chapterList.value[i]._content) return i
  }
  // 再补齐已加载区间内部的空缺（同样只补窗口内的）
  for (let i = firstLoaded; i <= lastLoaded && i <= horizon; i++) {
    if (!chapterList.value[i]._content) return i
  }
  return -1
}

// 获取回翻窗口内的第一个未加载章节：可见页往前 5 章为窗口下界，
// 从已加载头部向上找第一个缺口；窗口外（更靠前）的不预载。
// 可见页取不到时退化为「已加载头部 - 5 章」封顶
function getPrevUnloadedChapter() {
  let firstLoaded = chapterList.value.length
  for (let i = 0; i < chapterList.value.length; i++) {
    if (chapterList.value[i]._content) {
      firstLoaded = i
      break
    }
  }
  const visibleChapter = getVisibleChapter()
  const floor = visibleChapter < 0
    ? firstLoaded - LOOKAHEAD_CHAPTERS
    : visibleChapter - LOOKAHEAD_CHAPTERS
  for (let i = firstLoaded - 1; i >= 0 && i >= floor; i--) {
    if (!chapterList.value[i]._content) return i
  }
  return -1
}

// 回翻（往前/往上翻）预加载：同样向前查 5 章窗口，每次只发一个请求，
// 逐条往上补缺口，带滚动补偿（内容前插时阅读位置不跳）
let loadingPrev = false
async function loadPrevChapter() {
  if (loadingPrev) return
  loadingPrev = true
  try {
    await loadPrevChapterInternal()
  } finally {
    loadingPrev = false
  }
}

async function loadPrevChapterInternal() {
  // 查缺循环：每步补头部上方第一个缺口 → 补偿滚动位置 → 停顿 → 再往上查
  for (let guard = 0; guard < LOOKAHEAD_CHAPTERS + 2; guard++) {
    const idx = getPrevUnloadedChapter()
    if (idx < 0) return
    console.log('[loadPrevChapter] 开始加载章节 idx:', idx)
    // 记录加载前的滚动状态
    const el = scrollEl.value
    const prevScrollHeight = el?.scrollHeight || 0
    const prevScrollTop = el?.scrollTop || 0

    const success = await loadChapter(idx)
    if (!success) return
    rebuildSections()

    await nextTick()
    // 补偿滚动位置
    if (el) {
      const added = el.scrollHeight - prevScrollHeight
      el.scrollTop = prevScrollTop + added
    }
    // 等 DynamicScroller 内部 rAF 完成
    await new Promise(r => requestAnimationFrame(r))
    // 通知 DynamicScroller 重新计算可见项
    if (el) {
      el.dispatchEvent(new Event('scroll'))
    }
    await new Promise(r => requestAnimationFrame(r))
    // 二次修正（ResizeObserver 可能测量出新高度）
    if (el) {
      const added2 = el.scrollHeight - prevScrollHeight
      if (Math.abs(added2 - (el.scrollTop - prevScrollTop)) > 1) {
        el.scrollTop = prevScrollTop + added2
        el.dispatchEvent(new Event('scroll'))
        await new Promise(r => requestAnimationFrame(r))
      }
    }
    // 停一下再往上走：请求逐条发出，不会连成一片
    await new Promise(r => setTimeout(r, PRELOAD_STEP_DELAY))
  }
}

// TOC (目录) state
const tocVisible = ref(false)
const tocList = ref([])
const tocLoading = ref(false)
const tocActiveId = ref(null)

const docTitle = computed(() => props.doc?.title || '')
const docMeta = computed(() => props.doc?.meta || '')

// Initialize sections from doc HTML (API 失败时回退)
function initSections() {
  let items = []
  if (props.doc?.html) {
    const parser = new DOMParser()
    const dom = parser.parseFromString(props.doc.html, 'text/html')
    const secEls = dom.body.querySelectorAll('section.d-sec')
    items = Array.from(secEls).map((sec, i) => {
      const h = sec.querySelector('h2')
      const title = h ? h.textContent.replace(/^[一二三四五六七八九十]+、/, '') : `文本块 ${i + 1}`
      return {
        qtitle: clampBlockTitle(title),
        content: sec.innerHTML,
        flipped: false,
        minHeight: 0,
        editingTitle: false,
        aiGenerated: false,
        aiGenerating: false,
        compactFlip: false
      }
    })
  }
  sections.value = items
}

// ===== TOC (目录) =====
function toggleToc() {
  tocVisible.value = !tocVisible.value
  if (tocVisible.value) {
    // 打开目录时定位当前所在的章节
    if (isEditing.value) {
      // 编辑模式下当前章节即正在编辑的章
      const chId = editBlocks.value[0]?.chapterId
      tocActiveId.value = chId ?? null
    } else {
      const vCh = getVisibleChapter()
      tocActiveId.value = vCh >= 0 ? chapterList.value[vCh]?.id ?? null : null
    }
    if (tocList.value.length === 0) {
      loadToc()
    }
    scrollTocToActive()
  }
}

// 把当前章节那一行滚到目录面板可视区（只滚 toc-body，不影响外层页面）
function scrollTocToActive() {
  nextTick(() => {
    const container = isEditing.value ? editViewRef.value : docViewRef.value
    const item = container?.querySelector('.toc-item.active')
    const body = item?.closest('.toc-body')
    if (item && body) {
      const bodyRect = body.getBoundingClientRect()
      const itemRect = item.getBoundingClientRect()
      body.scrollTop += itemRect.top - bodyRect.top - (bodyRect.height - itemRect.height) / 2
    }
  })
}

function closeToc() {
  tocVisible.value = false
}

// 编辑模式下点击目录切换章节：有未保存内容时先提示保存
function handleEditTocClick(chapterId) {
  if (!chapterId) return
  if (isDirty.value) {
    pendingEditChapter = chapterId
    emit('open-unsaved')
    return
  }
  // 未修改 → 直接切换（不退出编辑，避免阅读视图闪一下）
  tocVisible.value = false
  switchEditChapter(chapterId)
}

// 跳转到指定章节并重新进入编辑模式
async function switchEditChapter(chapterId) {
  await jumpToChapter(chapterId)
  await nextTick()
  rebuildEditBlocksForChapter(chapterId)
}

// 在编辑状态下直接重建当前章的编辑块（不退出/重新进入编辑，避免视图闪烁）
function rebuildEditBlocksForChapter(chapterId) {
  const chIdx = chapterList.value.findIndex(ch => String(ch.id) === String(chapterId))
  if (chIdx < 0) return
  // 找到该章节的第一个内容块（跳过 chapterTitle）
  const firstSecIdx = sections.value.findIndex(s => s._chapterIdx === chIdx && s.type !== 'chapterTitle')
  if (firstSecIdx < 0) return
  // 向后找下一章标题作为结束
  let curEnd = sections.value.length
  for (let i = firstSecIdx + 1; i < sections.value.length; i++) {
    if (sections.value[i].type === 'chapterTitle') { curEnd = i; break }
  }
  const targetSections = sections.value.slice(firstSecIdx, curEnd).filter(sec => sec.type !== 'chapterTitle')

  isEditing.value = true
  isDirty.value = false
  isBatch.value = false
  batchMode.value = null
  brushOn.value = false
  // Reset block refs
  Object.keys(editBlockRefs).forEach(k => delete editBlockRefs[k])
  editBlocks.value = targetSections.map(sec => ({
    id: nextBlockId++,
    html: (() => {
      const html = renderMathInRichText(sec.content)
      return prepareEditHtml(html)
    })(),
    chapterId: sec.chapterId,
    picked: false,
    splitOpen: false,
    isTable: !!sec.isTable,
    txt: sec.txt || ''
  }))
  editSnapshot.value = getEditSnapshot()
  resetEditHistory()
  nextTick(() => {
    hideSelbar()
    syncEtool()
    initTableVditors()
    revealEditClozes()
  })
}

async function loadToc() {
  const collectionId = props.currentDoc
  if (!collectionId) return
  tocLoading.value = true
  try {
    const res = await bookApi.getChapterList({ collectionId })
    if (res.code !== 0) {
      flash(res.msg || '加载目录失败')
      return
    }
    if (Array.isArray(res.data)) {
      tocList.value = res.data
      if (tocVisible.value) scrollTocToActive()
    }
  } catch (err) {
    console.warn('加载目录失败', err)
    flash('网络异常，请稍后重试')
  }
  tocLoading.value = false
}

async function jumpToChapter(chapterId) {
  if (!chapterId) return
  tocVisible.value = false
  console.log('[jumpToChapter] 开始跳转, chapterId:', chapterId)
  // 容错：接口 id 可能是数字，目录传入的可能是字符串
  let targetIdx = chapterList.value.findIndex(ch => String(ch.id) === String(chapterId))
  console.log('[jumpToChapter] targetIdx:', targetIdx)
  if (targetIdx < 0) {
    // 本地章节列表未包含该章（如目录刚更新），重新拉取一次并合并
    try {
      const res = await bookApi.getChapterList({ collectionId: props.currentDoc })
      if (res.code === 0 && Array.isArray(res.data)) {
        const known = new Set(chapterList.value.map(ch => String(ch.id)))
        res.data.forEach(ch => {
          if (!known.has(String(ch.id))) chapterList.value.push({ ...ch, _content: null })
        })
        targetIdx = chapterList.value.findIndex(ch => String(ch.id) === String(chapterId))
      }
    } catch (err) {
      console.warn('[jumpToChapter] 重新拉取章节列表失败', err)
    }
  }
  if (targetIdx < 0) {
    console.warn('[jumpToChapter] 未找到章节', chapterId)
    return
  }

  isChapterJumping = true
  try {
    // 只保留目标章节附近的内容，清除其余已加载章节
    const keepStart = Math.max(0, targetIdx - 2)
    const keepEnd = Math.min(chapterList.value.length - 1, targetIdx + 3)
    for (let i = 0; i < chapterList.value.length; i++) {
      if (i < keepStart || i > keepEnd) {
        chapterList.value[i]._content = null
      }
    }

    // 加载目标章节及前后章节
    for (let i = keepStart; i <= keepEnd; i++) {
      if (!chapterList.value[i]._content) {
        await loadChapter(i)
      }
    }

    rebuildSections()
    await nextTick()

    // 等待两帧，确保 DOM 布局完全稳定
    await new Promise(r => requestAnimationFrame(r))
    await new Promise(r => requestAnimationFrame(r))

    // 滚动到目标章节的第一个 section。
    // DynamicScroller 是虚拟列表，目标（尤其最后一章）可能尚未渲染进 DOM，
    // 直接 querySelector + scrollIntoView 会落空。改用 scrollToItem 按累计高度
    // 定位，并循环校正直到目标元素真正渲染出来，再做一次精确对齐。
    const firstSecIdx = sections.value.findIndex(s => String(s.chapterId) === String(chapterId) && s.type !== 'chapterTitle')
    console.log('[jumpToChapter] firstSecIdx:', firstSecIdx)
    if (firstSecIdx < 0) return
    const displayIdx = displayItems.value.findIndex(it => it.index === firstSecIdx)
    if (displayIdx < 0 || !dPageRef.value) return

    let guard = 0
    let landed = false
    while (guard < 12) {
      const el = scrollEl.value?.querySelector(`[data-index="${firstSecIdx}"]`)
      if (el) {
        // 只移动内层滚动容器：scrollIntoView 会连带滚动所有祖先（外层布局容器），
        // 把整条头部（菜单/目录/编辑）滚出屏幕外
        if (scrollEl.value) {
          const scRect = scrollEl.value.getBoundingClientRect()
          const elRect = el.getBoundingClientRect()
          scrollEl.value.scrollTop += elRect.top - scRect.top
        }
        landed = true
        break
      }
      dPageRef.value.scrollToItem(displayIdx)
      await nextTick()
      await new Promise(r => requestAnimationFrame(r))
      guard++
    }
    if (!landed) {
      // 兜底：仍未渲染时按累计高度再定位一次
      dPageRef.value.scrollToItem(displayIdx)
    }
    console.log('[jumpToChapter] 定位完成, landed:', landed, 'displayIdx:', displayIdx, 'scrollTop:', scrollEl.value?.scrollTop)
  } finally {
    // 落地产生的滚动事件是异步派发的，可能在守卫重置后才到达；
    // 留一个冷却期，避免落地后立刻触发 loadPrev/loadNext 把前/后章节插入列表导致视图回弹
    const seq = ++chapterJumpSeq
    setTimeout(() => {
      if (chapterJumpSeq !== seq) return
      isChapterJumping = false
      // 落地后立即向前查缺：补载可见页之后第一个未加载页（尾部追加不影响已定位的位置），
      // 之后的页由 5 章窗口逐条往前补。回翻补载进行中时让位，保持一次一条请求
      if (!loadingPrev) loadNextChapter()
    }, 600)
  }
}

function flash(msg) {
  // 复用父组件的 flash
  emit('flash', msg)
}

// 进入页面时加载章节列表 + 第一章内容
let loadTimer = null
watch(() => props.currentDoc, async () => {
  isLoading.value = true
  readerPosReady = false
  clearTimeout(readerPosTimer)
  clearTimeout(loadTimer)
  const bookId = props.currentDoc
  if (!bookId) return

  // 重置状态
  sections.value = []
  allClozeRevealed.value = true
  clozeRevealByText = new Map()
  // 清空章节列表与加载队列
  chapterList.value = []
  chapterLoading.clear()

  // 尝试从 API 加载章节列表
  try {
    const res = await bookApi.getChapterList({ collectionId: bookId })
    if (res.code === 0 && Array.isArray(res.data) && res.data.length > 0) {
      // 保存章节列表，每项加上 _content 标记
      chapterList.value = res.data.map(ch => ({ ...ch, _content: null }))
      tocList.value = res.data
      // 只加载第一章并立即展示；之后的页由 5 章窗口在后台逐条往前预载（不阻塞打开）
      await loadChapter(0)
      rebuildSections()
      isLoading.value = false
      loadNextChapter()
      await restoreReaderPos(bookId)
      return
    }
  } catch (err) {
    console.warn('API 加载失败，使用 mock 数据', err)
  }

  // 回退：使用 doc 中的 html
  initSections()
  isLoading.value = false
  await restoreReaderPos(bookId)
}, { immediate: true })

// 手动输入的新文档自动进入编辑模式
watch(isLoading, (loading) => {
  if (!loading && props.autoEdit) {
    nextTick(() => {
      enterEdit()
      emit('edit-entered')
    })
  }
})

onUnmounted(() => {
  clearTimeout(loadTimer)
})

// Section flip
const readPointer = { x: 0, y: 0 }

function onSectionPointerDown(e) {
  if (e.button !== 0) return
  readPointer.x = e.clientX
  readPointer.y = e.clientY
}

function isTextDragOrSelect(e) {
  if (e) {
    const dx = Math.abs(e.clientX - readPointer.x)
    const dy = Math.abs(e.clientY - readPointer.y)
    if (dx > 5 || dy > 5) return true
  }
  const sel = window.getSelection()
  return !!(sel && String(sel).replace(/\s+/g, ''))
}

function toggleSectionFlip(i, event) {
  if (isTextDragOrSelect(event)) return
  if (event.target.closest('.kb-ai, .kb-fb, .kb-edit, .kb-q[contenteditable="true"], customclickablespan, a, button')) return
  const sec = sections.value[i]
  if (!sec.flipped) {
    const el = scrollEl.value?.querySelector(`[data-index="${i}"]`)
    if (el) {
      sec.minHeight = el.offsetHeight
      // 一两行（含矮表格）翻面后跟原文等高，藏掉「点击查看原文」以免挤
      sec.compactFlip = el.offsetHeight <= 120
    }
  }
  sec.flipped = !sec.flipped
}

// Title edit
const BLOCK_TITLE_MAX = 50

function clampBlockTitle(s) {
  return String(s || '').replace(/\s+/g, ' ').trim().slice(0, BLOCK_TITLE_MAX)
}

function setTitleCaretEnd(el) {
  const range = document.createRange()
  range.selectNodeContents(el)
  range.collapse(false)
  const sel = window.getSelection()
  sel.removeAllRanges()
  sel.addRange(range)
}

function onTitleBeforeInput(e) {
  if (e.isComposing) return
  if (e.inputType && (e.inputType.startsWith('delete') || e.inputType.startsWith('history'))) return
  if (e.inputType === 'insertCompositionText' || e.inputType === 'insertFromPaste') return
  const el = e.currentTarget
  const sel = window.getSelection()
  const selected = sel && sel.rangeCount ? sel.toString().length : 0
  const current = (el.textContent || '').length
  const room = BLOCK_TITLE_MAX - (current - selected)
  if (room <= 0) {
    e.preventDefault()
    return
  }
  if (e.inputType === 'insertText' && e.data && e.data.length > room) {
    e.preventDefault()
    document.execCommand('insertText', false, e.data.slice(0, room))
  }
}

function onTitlePaste(e) {
  e.preventDefault()
  const el = e.currentTarget
  const sel = window.getSelection()
  const selected = sel && sel.rangeCount ? sel.toString().length : 0
  const room = Math.max(0, BLOCK_TITLE_MAX - ((el.textContent || '').length - selected))
  const text = (e.clipboardData?.getData('text') || '').replace(/\s+/g, ' ').slice(0, room)
  if (text) document.execCommand('insertText', false, text)
}

function onTitleInput(e) {
  if (e.isComposing) return
  const el = e.currentTarget
  const raw = el.textContent || ''
  if (raw.length <= BLOCK_TITLE_MAX) return
  el.textContent = raw.slice(0, BLOCK_TITLE_MAX)
  setTitleCaretEnd(el)
}

function toggleTitleEdit(i) {
  const sec = sections.value[i]
  if (sec.aiGenerating) {
    emit('flash', 'AI正在生成标题中，请稍后再试')
    return
  }
  if (sec.editingTitle) {
    endTitleEdit(i, true)
  } else {
    sec.editingTitle = true
    nextTick(() => {
      const el = scrollEl.value?.querySelector(`[data-index="${i}"]`)
      const q = el?.querySelector('.kb-q')
      if (q) {
        q.focus()
        const range = document.createRange()
        range.selectNodeContents(q)
        const sel = window.getSelection()
        sel.removeAllRanges()
        sel.addRange(range)
      }
    })
  }
}

async function endTitleEdit(i, commit) {
  const sec = sections.value[i]
  if (!sec.editingTitle) return
  if (commit !== false) {
    const el = scrollEl.value?.querySelector(`[data-index="${i}"]`)
    const q = el?.querySelector('.kb-q')
    if (q) {
      const t = clampBlockTitle(q.textContent || '')
      if (t && t !== sec.qtitle) {
        sec.qtitle = t
        console.log('[endTitleEdit] 标题已更新, id:', sec.id, 'title:', t, 'chapterId:', sec.chapterId)
        // 调用后端更新分块标题
        if (sec.id) {
          try {
            const res = await bookApi.updateBlockTitle(sec.id, t, sec.chapterId)
            console.log('[endTitleEdit] API响应:', res)
            if (res.code !== 0) {
              emit('flash', res.msg || '标题更新失败')
            }
          } catch (err) {
            console.warn('更新标题失败', err)
            emit('flash', '网络异常，标题更新失败')
          }
        } else {
          console.warn('[endTitleEdit] sec.id 为空，跳过API调用')
        }
      } else {
        sec.qtitle = t || sec.qtitle
      }
    }
  }
  sec.editingTitle = false
}

async function genAiTitle(i) {
  const sec = sections.value[i]
  if (!sec || sec.aiGenerating) return
  if (sec.editingTitle) endTitleEdit(i, false)
  sec.aiGenerating = true
  if (!sec.id) {
    await delayMs(1200)
    if (sec.aiGenerating) {
      sec.aiGenerated = true
      sec.aiGenerating = false
      emit('flash', '已由 AI 生成标题')
    }
    return
  }
  try {
    const res = await bookApi.aiGenerateBlockTitle(sec.id)
    if (!sec.aiGenerating) return
    if (res.code !== 0) {
      sec.aiGenerating = false
      emit('flash', res.msg || 'AI 生成标题失败')
      return
    }
    const fromRes = pickAiTitle(res)
    if (fromRes) {
      sec.qtitle = clampBlockTitle(fromRes)
      sec.aiGenerated = true
      sec.aiGenerating = false
      emit('flash', '已由 AI 生成标题')
      return
    }
    await pollAiBlockTitle(sec)
  } catch (err) {
    console.warn('AI 生成标题失败', err)
    sec.aiGenerating = false
    emit('flash', '网络异常，请稍后重试')
  }
}

function pickAiTitle(res) {
  const d = res && res.data
  if (typeof d === 'string') return d.trim()
  if (!d || typeof d !== 'object') return ''
  return String(d.title || d.blockTitle || d.qtitle || '').trim()
}

const aiTitleTimers = new Set()
function delayMs(ms) {
  return new Promise(resolve => {
    const t = setTimeout(() => {
      aiTitleTimers.delete(t)
      resolve()
    }, ms)
    aiTitleTimers.add(t)
  })
}

async function pollAiBlockTitle(sec) {
  const oldTitle = sec.qtitle
  for (let n = 0; n < 15; n++) {
    await delayMs(2000)
    if (!sec.aiGenerating) return
    if (!sec.chapterId) continue
    try {
      const detail = await bookApi.getDetail({ id: sec.chapterId })
      const blk = detail.data?.bookDataList?.find(b => b.id === sec.id)
      const next = blk && blk.title
      if (next && next !== oldTitle) {
        sec.qtitle = clampBlockTitle(next)
        sec.aiGenerated = true
        sec.aiGenerating = false
        emit('flash', '已由 AI 生成标题')
        return
      }
    } catch (err) {
      console.warn('轮询 AI 标题失败', err)
    }
  }
  sec.aiGenerating = false
  emit('flash', '标题生成超时，请刷新后重试')
}

// Cloze toggle in reading mode
function toggleClozeSpan(event) {
  if (isEditing.value) return
  const c = event.target.closest('customclickablespan')
  if (!c) return
  const group = c.getAttribute('data-cloze-group')
  let targets = [c]
  if (group) {
    const scope = c.closest('.kb-back') || scrollEl.value
    if (scope) {
      targets = [...scope.querySelectorAll(`${CLOZE_TAG}[data-cloze-group="${CSS.escape(group)}"]`)]
    }
  }
  const show = !c.classList.contains('shown')
  targets.forEach(el => el.classList.toggle('shown', show))
}

function applyClozeRevealState(root, shown = allClozeRevealed.value) {
  if (!root?.querySelectorAll) return
  root.querySelectorAll('customclickablespan').forEach(el => {
    el.classList.toggle('shown', shown)
  })
}

function clozeRevealKey(el) {
  return (el.textContent || '').replace(/\s+/g, ' ').trim()
}

function captureClozeRevealState() {
  clozeRevealByText = new Map()
  const root = scrollEl.value
  if (!root) return
  root.querySelectorAll('.kb-back customclickablespan').forEach(el => {
    const key = clozeRevealKey(el)
    if (!key) return
    if (clozeRevealByText.get(key) === true) return
    clozeRevealByText.set(key, el.classList.contains('shown'))
  })
}

function hydrateReaderClozes(root) {
  if (!root?.querySelectorAll) return
  const fallback = allClozeRevealed.value
  const hasSnap = clozeRevealByText.size > 0
  root.querySelectorAll('customclickablespan').forEach(el => {
    const key = clozeRevealKey(el)
    const shown = hasSnap && clozeRevealByText.has(key) ? clozeRevealByText.get(key) : fallback
    el.classList.toggle('shown', shown)
  })
}

function toggleAllCloze() {
  allClozeRevealed.value = !allClozeRevealed.value
  applyClozeRevealState(scrollEl.value, allClozeRevealed.value)
}

// Cloze Bubble (reading mode)
const clozeBubbleVisible = ref(false)
const clozeBubbleBelow = ref(false)
const clozeBubbleStyle = ref({})
let readClozeRange = null
let savedReadRange = null  // 备份，hideClozeBubble 时不清除

function selectionInDocBody() {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || !sel.rangeCount) return null
  if (!String(sel).replace(/\s+/g, '')) return null
  const range = sel.getRangeAt(0)
  const startEl = hostOf(range.startContainer)
  const endEl = hostOf(range.endContainer)
  if (!startEl?.closest || !endEl?.closest) return null
  if (!startEl.closest('#docBody')) return null
  // 分块翻转后的标题面不能挖空，气泡只出现在原文（.kb-back）
  const startBack = startEl.closest('.kb-back')
  const endBack = endEl.closest('.kb-back')
  if (!startBack || startBack !== endBack) return null
  if (startEl.closest('.kb-front') || endEl.closest('.kb-front')) return null
  return sel
}

function placeClozeBubble() {
  if (isEditing.value) { hideClozeBubble(); return }
  const sel = selectionInDocBody()
  if (!sel) { hideClozeBubble(); return }
  readClozeRange = sel.getRangeAt(0).cloneRange()
  savedReadRange = readClozeRange
  const rect = readClozeRange.getBoundingClientRect()
  if (!rect || (rect.width === 0 && rect.height === 0)) { hideClozeBubble(); return }
  clozeBubbleVisible.value = true
  const bw = 72
  const bh = 40
  const left = rect.left + rect.width / 2 - bw / 2
  const top = rect.top - bh - 12
  clozeBubbleBelow.value = top < 56
  if (clozeBubbleBelow.value) {
    clozeBubbleStyle.value = { left: Math.max(12, Math.min(left, window.innerWidth - bw - 12)) + 'px', top: (rect.bottom + 12) + 'px' }
  } else {
    clozeBubbleStyle.value = { left: Math.max(12, Math.min(left, window.innerWidth - bw - 12)) + 'px', top: top + 'px' }
  }
}

function hideClozeBubble() {
  clozeBubbleVisible.value = false
  readClozeRange = null
}

const CLOZE_TAG = 'customclickablespan'
const CLOZE_BLOCK_SEL = 'p, div, li, h1, h2, h3, h4, h5, h6, td, th, blockquote, pre, section, article'
let clozeGroupSeq = 0

function createClozeGroupId() {
  clozeGroupSeq += 1
  return `cg-${Date.now()}-${clozeGroupSeq}`
}

function isClozeElement(el) {
  return el?.nodeType === 1 && el.localName === CLOZE_TAG
}

/** 同组且相邻的挖空合并为一个标签（中间空白文本节点也并入） */
function mergeAdjacentClozeGroups(root) {
  if (!root?.querySelectorAll) return
  const parents = new Set()
  root.querySelectorAll(CLOZE_TAG).forEach(el => {
    if (el.parentElement) parents.add(el.parentElement)
  })
  parents.forEach(parent => {
    let node = parent.firstChild
    while (node) {
      if (isClozeElement(node)) {
        const group = node.getAttribute('data-cloze-group')
        if (!group) {
          node = node.nextSibling
          continue
        }
        let scan = node.nextSibling
        while (scan) {
          if (scan.nodeType === 3 && !normalizeClozeText(scan.textContent)) {
            scan = scan.nextSibling
            continue
          }
          if (isClozeElement(scan) && scan.getAttribute('data-cloze-group') === group) {
            let between = node.nextSibling
            while (between && between !== scan) {
              const move = between
              between = between.nextSibling
              node.appendChild(move)
            }
            while (scan.firstChild) node.appendChild(scan.firstChild)
            const remove = scan
            scan = scan.nextSibling
            remove.remove()
            continue
          }
          break
        }
      }
      node = node.nextSibling
    }
  })
}

/** 同组挖空可能在 detach 后变成非相邻节点，按块内顺序合并为单一标签 */
function consolidateClozeGroupInBlock(groupId, block) {
  if (!groupId || !block) return
  const spans = [...block.querySelectorAll(`${CLOZE_TAG}[data-cloze-group="${CSS.escape(groupId)}"]`)]
  if (spans.length < 2) return
  spans.sort((a, b) => {
    const pos = a.compareDocumentPosition(b)
    if (pos & Node.DOCUMENT_POSITION_FOLLOWING) return -1
    if (pos & Node.DOCUMENT_POSITION_PRECEDING) return 1
    return 0
  })
  const first = spans[0]
  const hadShown = spans.some(s => s.classList.contains('shown'))
  for (let i = 1; i < spans.length; i++) {
    const el = spans[i]
    if (el.parentNode !== first.parentNode) continue
    let n = first.nextSibling
    while (n && n !== el) {
      const move = n
      n = n.nextSibling
      first.appendChild(move)
    }
    while (el.firstChild) first.appendChild(el.firstChild)
    el.remove()
  }
  if (hadShown) first.classList.add('shown')
}

function consolidateAllClozeGroups(root) {
  if (!root?.querySelectorAll) return
  const block = root.closest?.('.kb-back') || root.closest?.('.eblk-txt') || root
  const groups = new Set()
  root.querySelectorAll(`${CLOZE_TAG}[data-cloze-group]`).forEach(el => {
    const gid = el.getAttribute('data-cloze-group')
    if (gid) groups.add(gid)
  })
  groups.forEach(gid => consolidateClozeGroupInBlock(gid, block))
  mergeAdjacentClozeGroups(root)
}

function hostOf(node) {
  return node && (node.nodeType === 1 ? node : node.parentElement)
}

function unwrapCloze(el) {
  const parent = el?.parentNode
  if (!parent) return
  const preBold = el.getAttribute('data-pre-bold') === '1'
  const frag = document.createDocumentFragment()
  while (el.firstChild) frag.appendChild(el.firstChild)
  stripAutoBoldFromFragment(frag)
  if (preBold) ensureFragmentBold(frag, true)
  parent.replaceChild(frag, el)
}

function unwrapInlineTag(el) {
  unwrapCloze(el)
}

const INLINE_DECO_TAGS = {
  underline: { tag: 'U', query: 'underline' },
  strikeThrough: { tag: 'S', query: 'strikeThrough' },
}

function selectionFullyWrappedIn(range, tagName) {
  const startEl = hostOf(range.startContainer)
  const endEl = hostOf(range.endContainer)
  if (!startEl || !endEl) return null
  const startWrap = startEl.closest(tagName)
  const endWrap = endEl.closest(tagName)
  if (!startWrap || startWrap !== endWrap) return null
  if (String(range) === (startWrap.textContent || '')) return startWrap
  return null
}

function refreshSavedRange() {
  const sel = window.getSelection()
  if (!sel?.rangeCount || sel.isCollapsed) return
  try {
    savedRange = sel.getRangeAt(0).cloneRange()
    toolbarRange = savedRange.cloneRange()
  } catch {}
}

function rememberToolbarRange() {
  pinSelbarAction()
}

function getBlockForRange(range) {
  if (!range) return null
  return hostOf(range.startContainer)?.closest?.('.eblk-txt, .kb-back') || null
}

function rangeToOffsets(range, block) {
  if (!range || !block) return null
  try {
    const pre = document.createRange()
    pre.selectNodeContents(block)
    pre.setEnd(range.startContainer, range.startOffset)
    const start = pre.toString().length
    pre.setEnd(range.endContainer, range.endOffset)
    const end = pre.toString().length
    return { block, start, end, text: range.toString() }
  } catch {
    return null
  }
}

function offsetsToRange(meta) {
  if (!meta?.block) return null
  const { block, start, end } = meta
  let acc = 0
  let sNode = null
  let sOff = 0
  let eNode = null
  let eOff = 0
  const walker = document.createTreeWalker(meta.block, NodeFilter.SHOW_TEXT)
  let node
  while ((node = walker.nextNode())) {
    const len = (node.data || '').length
    // 起点刚好位于两个文本节点的边界时，必须落到后一个节点的 0 位置。
    // 若用 >=，格式包裹后会落到前一个节点末尾，导致 <u>/<s> 激活态误判，
    // 再次点击时继续嵌套标签而不是取消格式。
    if (sNode === null && acc + len > start) {
      sNode = node
      sOff = Math.max(0, start - acc)
    }
    if (acc + len >= end) {
      eNode = node
      eOff = Math.max(0, end - acc)
      break
    }
    acc += len
  }
  if (!sNode || !eNode) return null
  const range = document.createRange()
  range.setStart(sNode, sOff)
  range.setEnd(eNode, eOff)
  return range
}

let toolbarSelMeta = null
let selbarPinned = false
let selbarInteractTimer = 0

function saveToolbarSelMeta() {
  const range = toolbarRange || savedRange
  if (!range) { toolbarSelMeta = null; return }
  toolbarSelMeta = rangeToOffsets(range, getBlockForRange(range))
}

function pinSelbarAction() {
  selbarPinned = true
  selbarInteracting = true
  if (savedRange) toolbarRange = savedRange.cloneRange()
  else refreshSavedRange()
  saveToolbarSelMeta()
  clearTimeout(selbarInteractTimer)
  selbarInteractTimer = window.setTimeout(() => { selbarInteracting = false }, 500)
}

function restoreToolbarSelection() {
  if (toolbarSelMeta) {
    const range = offsetsToRange(toolbarSelMeta)
    if (range && !range.collapsed) {
      const sel = window.getSelection()
      sel.removeAllRanges()
      sel.addRange(range)
      savedRange = range.cloneRange()
      toolbarRange = range.cloneRange()
      return true
    }
  }
  return restoreToolbarRange()
}

function positionSelbarAtRange(range) {
  if (!range) return false
  const rect = range.getBoundingClientRect()
  if (!rect || (rect.width === 0 && rect.height === 0)) return false
  selbarVisible.value = true
  const bw = selbarRef.value?.offsetWidth || 400
  const bh = 40
  const left = rect.left + rect.width / 2 - bw / 2
  const top = rect.top - bh - 12
  selbarBelow.value = top < 56
  if (selbarBelow.value) {
    selbarStyle.value = { left: Math.max(12, Math.min(left, window.innerWidth - bw - 12)) + 'px', top: (rect.bottom + 12) + 'px' }
  } else {
    selbarStyle.value = { left: Math.max(12, Math.min(left, window.innerWidth - bw - 12)) + 'px', top: top + 'px' }
  }
  updateSelbarActive()
  return true
}

function showSelbarPinned() {
  if (!isEditing.value || brushOn.value || selInVditor()) return
  restoreToolbarSelection()
  const sel = window.getSelection()
  if (sel?.rangeCount && !sel.isCollapsed) {
    if (positionSelbarAtRange(sel.getRangeAt(0))) return
  }
  if (toolbarSelMeta) {
    const range = offsetsToRange(toolbarSelMeta)
    if (range) positionSelbarAtRange(range)
  }
}

function finishFormatAction(keepSelbar = true) {
  syncActiveBlockHtml()
  restoreToolbarSelection()
  refreshSavedRange()
  saveToolbarSelMeta()
  updateSelbarActive()
  syncEtool()
  if (keepSelbar) {
    selbarPinned = true
    nextTick(() => showSelbarPinned())
  }
}

function restoreToolbarRange() {
  const range = toolbarRange || savedRange
  if (!range) return false
  try {
    const sel = window.getSelection()
    sel.removeAllRanges()
    sel.addRange(range)
    return !!sel.rangeCount && !sel.isCollapsed
  } catch {
    return false
  }
}

function wrapRangeWithTag(range, tagName) {
  const el = document.createElement(tagName)
  try {
    range.surroundContents(el)
  } catch {
    el.appendChild(range.extractContents())
    range.insertNode(el)
  }
  return el
}

function expandDecoTags(tagName) {
  if (tagName === 'S') return ['S', 'STRIKE', 'DEL']
  if (tagName === 'U') return ['U']
  return [tagName]
}

function collectDecoElementsInRange(range, tagNames) {
  const block = hostOf(range.commonAncestorContainer)?.closest?.('.eblk-txt')
    || hostOf(range.startContainer)?.closest?.('.eblk-txt')
  if (!block) return []
  const found = new Set()
  for (const name of tagNames) {
    block.querySelectorAll(name).forEach(el => {
      try {
        if (range.intersectsNode(el)) found.add(el)
      } catch {}
    })
  }
  if (tagNames.includes('S') || tagNames.includes('STRIKE') || tagNames.includes('DEL')) {
    block.querySelectorAll('span[style]').forEach(el => {
      const td = el.style?.textDecoration || ''
      if (td.includes('line-through') && range.intersectsNode(el)) found.add(el)
    })
  }
  if (tagNames.includes('U')) {
    block.querySelectorAll('span[style]').forEach(el => {
      const td = el.style?.textDecoration || ''
      if (td.includes('underline') && range.intersectsNode(el)) found.add(el)
    })
  }
  return [...found].sort((a, b) => {
    if (a.contains(b)) return 1
    if (b.contains(a)) return -1
    return 0
  })
}

function selectionHasDeco(range, tagName) {
  if (!range || range.collapsed) return false
  const tags = expandDecoTags(tagName)
  if (tags.some(t => selectionFullyWrappedIn(range, t))) return true
  return collectDecoElementsInRange(range, tags).length > 0
}

function splitRangeAtClozeEdges(range) {
  const startCloze = hostOf(range.startContainer)?.closest?.(CLOZE_TAG)
  const endCloze = hostOf(range.endContainer)?.closest?.(CLOZE_TAG)
  if (startCloze === endCloze) return [range]

  const block = hostOf(range.startContainer)?.closest?.('.eblk-txt')
  if (!block) return [range]

  const pieces = []
  let groupStart = null
  let groupEnd = null
  let groupCloze = undefined

  const flush = () => {
    if (!groupStart || !groupEnd) return
    const r = document.createRange()
    r.setStart(groupStart.node, groupStart.offset)
    r.setEnd(groupEnd.node, groupEnd.offset)
    if (String(r).replace(/\s/g, '')) pieces.push(r)
    groupStart = groupEnd = null
    groupCloze = undefined
  }

  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      try {
        return range.intersectsNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
      } catch {
        return NodeFilter.FILTER_REJECT
      }
    },
  })

  let node
  while ((node = walker.nextNode())) {
    const cloze = node.parentElement?.closest?.(CLOZE_TAG) || null
    let startOff = 0
    let endOff = node.length
    if (node === range.startContainer) startOff = range.startOffset
    if (node === range.endContainer) endOff = range.endOffset
    if (startOff >= endOff) continue

    if (groupCloze === undefined) {
      groupCloze = cloze
      groupStart = { node, offset: startOff }
      groupEnd = { node, offset: endOff }
    } else if (groupCloze === cloze) {
      groupEnd = { node, offset: endOff }
    } else {
      flush()
      groupCloze = cloze
      groupStart = { node, offset: startOff }
      groupEnd = { node, offset: endOff }
    }
  }
  flush()
  return pieces.length ? pieces : [range]
}

function splitRangeForDeco(range) {
  const pieces = []
  splitRangeByBlocks(range).forEach(part => {
    splitRangeAtClozeEdges(part).forEach(p => pieces.push(p))
  })
  return pieces.length ? pieces : [range]
}

function clozeRootsInRange(range) {
  const roots = new Set()
  const block = hostOf(range.startContainer)?.closest?.('.eblk-txt')
  if (!block) return roots
  block.querySelectorAll(CLOZE_TAG).forEach(cloze => {
    try {
      if (range.intersectsNode(cloze)) roots.add(cloze)
    } catch {}
  })
  return roots
}

function normalizeDecoInClozes(range) {
  clozeRootsInRange(range).forEach(isolateClozeDecorations)
}

function unwrapDecoInRange(range, tagName) {
  const tags = expandDecoTags(tagName)
  for (let i = 0; i < 24; i++) {
    const els = collectDecoElementsInRange(range, tags)
    if (!els.length) break
    ;[...els].reverse().forEach(unwrapInlineTag)
  }
}

function unwrapDecoInRanges(ranges, tagName) {
  ranges.forEach(r => unwrapDecoInRange(r, tagName))
}

function wrapDecoRanges(ranges, tagName) {
  const wrapped = []
  ranges.forEach(r => {
    if (!String(r).replace(/\s/g, '')) return
    wrapped.push(wrapRangeWithTag(r, tagName))
  })
  return wrapped
}

function getFormatRange() {
  if (toolbarRange) {
    try { return toolbarRange.cloneRange() } catch {}
  }
  const sel = window.getSelection()
  if (sel?.rangeCount && !sel.isCollapsed) return sel.getRangeAt(0).cloneRange()
  if (savedRange) {
    try { return savedRange.cloneRange() } catch {}
  }
  return null
}

function syncActiveBlockHtml() {
  const range = toolbarRange || savedRange
  let el = null
  if (range) el = hostOf(range.startContainer)?.closest?.('.eblk-txt')
  if (!el) {
    const sel = window.getSelection()
    if (sel?.anchorNode) el = hostOf(sel.anchorNode)?.closest?.('.eblk-txt')
  }
  if (!el) return
  const idx = Object.keys(editBlockRefs).find(k => editBlockRefs[k] === el)
  if (idx == null) return
  editBlocks.value[idx].html = el.innerHTML
  el.dispatchEvent(new Event('input', { bubbles: true }))
}

function finishSelbarAction() {
  finishFormatAction(true)
}

function inlineDecoActive(cmd) {
  const spec = INLINE_DECO_TAGS[cmd]
  if (!spec) return false
  const range = getFormatRange()
  if (!range) return false
  return selectionHasDeco(range, spec.tag)
}

function isUserBoldElement(el) {
  if (!el || el.nodeType !== 1) return false
  if (el.tagName !== 'B' && el.tagName !== 'STRONG') return false
  return !el.hasAttribute('data-cloze-auto-bold')
}

function nodeHasUserBold(node) {
  let el = hostOf(node)
  while (el && !el.classList?.contains('eblk-txt')) {
    if (isUserBoldElement(el)) return true
    el = el.parentElement
  }
  return false
}

function headingOf(node) {
  const el = hostOf(node)
  const heading = el?.closest?.('h1, h2, h3')
  return heading?.closest?.('.eblk-txt, #editBody') ? heading : null
}

function isExplicitUnboldNode(node) {
  let el = hostOf(node)
  while (el && !el.classList?.contains('eblk-txt')) {
    if (el.hasAttribute?.('data-user-unbold')) return true
    const w = el.style?.fontWeight
    if (w === 'normal' || w === '400') return true
    el = el.parentElement
  }
  return false
}

function nodeLooksUserBold(node) {
  if (nodeHasUserBold(node)) return true
  return !!(headingOf(node) && !isExplicitUnboldNode(node))
}

/** 工具栏加粗选中态：用户 <b>，或标题默认加粗（未显式取消） */
function isUserBoldActive() {
  const sel = window.getSelection()
  if (!sel?.rangeCount) return false
  const anchor = sel.anchorNode
  if (!hostOf(anchor)?.closest?.('#editBody, .eblk-txt')) return false
  const range = sel.getRangeAt(0)
  if (range.collapsed) return nodeLooksUserBold(range.startContainer)

  const block = getBlockForRange(range) || hostOf(range.commonAncestorContainer)
  if (!block) return nodeLooksUserBold(range.startContainer)
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      try {
        return range.intersectsNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
      } catch {
        return NodeFilter.FILTER_REJECT
      }
    },
  })
  let hasText = false
  let node
  while ((node = walker.nextNode())) {
    if (!node.textContent?.trim()) continue
    hasText = true
    if (!nodeLooksUserBold(node)) return false
  }
  return hasText
}

function expandRangeForBold() {
  const sel = window.getSelection()
  if (sel?.rangeCount && !sel.isCollapsed) return sel.getRangeAt(0).cloneRange()
  if (toolbarRange && !toolbarRange.collapsed) {
    try {
      sel.removeAllRanges()
      sel.addRange(toolbarRange)
      return toolbarRange.cloneRange()
    } catch {}
  }
  const node = sel?.anchorNode || savedRange?.startContainer
  const el = hostOf(node)
  if (!el?.closest?.('.eblk-txt, #editBody')) return null
  const block = el.closest('h1, h2, h3, p, li') || el.closest('.eblk-txt')
  if (!block) return null
  const r = document.createRange()
  r.selectNodeContents(block)
  sel.removeAllRanges()
  sel.addRange(r)
  return r
}

function unwrapUserBoldInRange(range) {
  const block = getBlockForRange(range)
  if (!block) return
  ;[...block.querySelectorAll('b, strong')].reverse().forEach(el => {
    if (!isUserBoldElement(el)) return
    try { if (range.intersectsNode(el)) unwrapInlineTag(el) } catch {}
  })
}

function unwrapUserUnboldInRange(range) {
  const block = getBlockForRange(range)
  if (!block) return
  ;[...block.querySelectorAll('[data-user-unbold]')].reverse().forEach(el => {
    try { if (range.intersectsNode(el)) unwrapInlineTag(el) } catch {}
  })
}

function liveBoldRange(fallback) {
  const sel = window.getSelection()
  if (sel?.rangeCount) return sel.getRangeAt(0)
  return fallback
}

function toggleInlineDecoration(cmd, keepSelbar = true) {
  pinSelbarAction()
  if (!restoreToolbarSelection()) restoreRange()
  const spec = INLINE_DECO_TAGS[cmd]
  if (!spec) return false
  const sel = window.getSelection()
  if (!sel?.rangeCount || sel.isCollapsed) return false
  const range = sel.getRangeAt(0).cloneRange()
  const rootEl = hostOf(range.commonAncestorContainer)
  if (!rootEl?.closest?.('#editBody')) return false
  pushEditHistory()

  const parts = splitRangeForDeco(range)
  if (selectionHasDeco(range, spec.tag)) {
    unwrapDecoInRanges(parts, spec.tag)
  } else {
    const wrapped = wrapDecoRanges(parts, spec.tag)
    if (wrapped.length) {
      const newRange = document.createRange()
      newRange.setStartBefore(wrapped[0])
      newRange.setEndAfter(wrapped[wrapped.length - 1])
      sel.removeAllRanges()
      sel.addRange(newRange)
    }
  }

  normalizeDecoInClozes(range)
  finishFormatAction(keepSelbar)
  closeEtoolPops()
  return true
}

function flattenNestedClozes(root) {
  if (!root) return
  let nested
  while ((nested = root.querySelector(`${CLOZE_TAG} ${CLOZE_TAG}`))) {
    unwrapCloze(nested)
  }
}

const DECO_TAGS = new Set(['U', 'S', 'STRIKE', 'DEL'])

function hasInlineTextDecoration(el) {
  if (!el || el.nodeType !== 1 || el.tagName !== 'SPAN') return false
  const td = el.style?.textDecoration || ''
  return td && td !== 'none'
}

function isColorWrapper(el) {
  if (!el || el.nodeType !== 1) return false
  if (el.tagName === CLOZE_TAG) return false
  if (el.tagName === 'FONT' && el.getAttribute('color')) return true
  const c = (el.style?.color || '').replace(/\s/g, '').toLowerCase()
  return !!(c && c !== 'transparent' && c !== 'rgba(0,0,0,0)')
}

function isDecoElement(el) {
  if (!el || el.nodeType !== 1) return false
  if (DECO_TAGS.has(el.tagName)) return true
  if (isColorWrapper(el)) return true
  return hasInlineTextDecoration(el)
}

function rangeTextColor(range) {
  const el = hostOf(range?.startContainer)
  if (!el || typeof getComputedStyle !== 'function') return ''
  const color = getComputedStyle(el).color || ''
  const norm = color.replace(/\s/g, '').toLowerCase()
  if (!norm || norm === 'transparent' || norm === 'rgba(0,0,0,0)') return ''
  return color
}

/** 把包裹挖空 span 的下划线/删除线等装饰标签拆到 span 内部，避免隐藏文字后装饰线仍可见 */
function isolateClozeDecorations(span) {
  if (!span?.parentElement) return
  let parent = span.parentElement
  while (parent && isDecoElement(parent)) {
    const deco = parent
    const grand = deco.parentNode
    if (!grand) break

    const before = document.createDocumentFragment()
    const after = document.createDocumentFragment()

    let node = deco.firstChild
    while (node && node !== span) {
      const next = node.nextSibling
      before.appendChild(node)
      node = next
    }

    node = span.nextSibling
    while (node) {
      const next = node.nextSibling
      after.appendChild(node)
      node = next
    }

    const innerDeco = deco.cloneNode(false)
    while (span.firstChild) innerDeco.appendChild(span.firstChild)
    span.appendChild(innerDeco)

    deco.removeChild(span)

    const replaceFrag = document.createDocumentFragment()
    if (before.childNodes.length) {
      const beforeWrap = deco.cloneNode(false)
      beforeWrap.appendChild(before)
      replaceFrag.appendChild(beforeWrap)
    }
    replaceFrag.appendChild(span)
    if (after.childNodes.length) {
      const afterWrap = deco.cloneNode(false)
      afterWrap.appendChild(after)
      replaceFrag.appendChild(afterWrap)
    }

    grand.replaceChild(replaceFrag, deco)
    parent = span.parentElement
  }
}

function isContentFullyBold(container) {
  if (!container) return false
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT)
  let node
  let hasText = false
  while ((node = walker.nextNode())) {
    if (!node.textContent?.trim()) continue
    hasText = true
    const boldEl = node.parentElement?.closest?.('b, strong')
    if (!boldEl || !container.contains(boldEl)) return false
  }
  return hasText
}

function isClozeFullyBold(span) {
  return isContentFullyBold(span)
}

function isRangeFullyBold(range) {
  if (!range || range.collapsed) return false
  try {
    const probe = document.createElement('div')
    probe.appendChild(range.cloneContents())
    return isContentFullyBold(probe)
  } catch {
    return false
  }
}

function stripAutoBoldFromFragment(frag) {
  if (!frag) return
  let changed = true
  while (changed) {
    changed = false
    frag.querySelectorAll('b[data-cloze-auto-bold], strong[data-cloze-auto-bold]').forEach(b => {
      const p = b.parentNode
      if (!p) return
      while (b.firstChild) p.insertBefore(b.firstChild, b)
      p.removeChild(b)
      changed = true
    })
    if (frag.childNodes.length === 1) {
      const only = frag.firstChild
      if (only?.nodeType === 1 && (only.tagName === 'B' || only.tagName === 'STRONG') && only.hasAttribute('data-cloze-auto-bold')) {
        while (only.firstChild) frag.insertBefore(only.firstChild, only)
        frag.removeChild(only)
        changed = true
      }
    }
  }
}

function ensureFragmentBold(frag, bold) {
  if (!frag || !bold) return
  const probe = document.createElement('div')
  probe.appendChild(frag.cloneNode(true))
  if (isContentFullyBold(probe)) return
  const b = document.createElement('b')
  while (frag.firstChild) b.appendChild(frag.firstChild)
  frag.appendChild(b)
}

function cloneClozeShell(cloze) {
  const span = document.createElement(CLOZE_TAG)
  if (cloze.className) span.className = cloze.className
  const preBold = cloze.getAttribute('data-pre-bold')
  if (preBold) span.setAttribute('data-pre-bold', preBold)
  if (cloze.hasAttribute('data-cloze-unbold')) span.setAttribute('data-cloze-unbold', '')
  if (cloze.style?.color) span.style.color = cloze.style.color
  return span
}

function isFullClozeSelection(range, cloze) {
  try {
    const full = document.createRange()
    full.selectNodeContents(cloze)
    return range.compareBoundaryPoints(Range.START_TO_START, full) === 0
      && range.compareBoundaryPoints(Range.END_TO_END, full) === 0
  } catch {
    return false
  }
}

function normalizeClozeText(text) {
  return (text || '').replace(/[\u200b\uFEFF]/g, '').replace(/\s+/g, '')
}

function isEffectivelyEmptyCloze(el) {
  if (!el) return true
  if (normalizeClozeText(el.textContent)) return false
  return !el.querySelector('img, .math, latex-formula, table')
}

function cleanupEmptyClozes(root) {
  if (!root?.querySelectorAll) return
  root.querySelectorAll(CLOZE_TAG).forEach(el => {
    if (isEffectivelyEmptyCloze(el)) el.remove()
  })
}

function normalizeUnclozeFragment(frag, preBold) {
  stripAutoBoldFromFragment(frag)
  if (preBold) ensureFragmentBold(frag, true)
}

function appendFragmentNodes(frag, parent, ref) {
  if (!frag || !parent) return
  while (frag.firstChild) parent.insertBefore(frag.firstChild, ref)
}
function unwrapPartialClozeRange(range, cloze) {
  const parent = cloze.parentNode
  if (!parent) return

  const preBold = cloze.getAttribute('data-pre-bold') === '1'
  const insertBefore = cloze.nextSibling

  const afterRange = document.createRange()
  afterRange.setStart(range.endContainer, range.endOffset)
  afterRange.setEnd(cloze, cloze.childNodes.length)
  const afterPart = afterRange.extractContents()
  const middle = range.extractContents()

  const beforeText = normalizeClozeText(cloze.textContent)
  const afterText = normalizeClozeText(afterPart.textContent)
  const midText = normalizeClozeText(middle.textContent)

  if (midText) {
    normalizeUnclozeFragment(middle, preBold)
    parent.insertBefore(middle, insertBefore)
  }

  if (afterText) {
    const afterCloze = cloneClozeShell(cloze)
    afterCloze.appendChild(afterPart)
    isolateClozeDecorations(afterCloze)
    applyDefaultClozeBold(afterCloze)
    parent.insertBefore(afterCloze, insertBefore)
  } else {
    appendFragmentNodes(afterPart, parent, insertBefore)
  }

  if (!beforeText) parent.removeChild(cloze)
  else if (isEffectivelyEmptyCloze(cloze)) parent.removeChild(cloze)

  cleanupEmptyClozes(parent)
}

/** 新建挖空时默认加粗；编辑页可通过取消加粗移除 <b>，阅读页仍由 CSS 强制粗体 */
function applyDefaultClozeBold(span) {
  if (!span || isClozeFullyBold(span)) return
  span.removeAttribute('data-cloze-unbold')
  const b = document.createElement('b')
  b.setAttribute('data-cloze-auto-bold', '')
  while (span.firstChild) b.appendChild(span.firstChild)
  span.appendChild(b)
}

function migrateClozeBold(span) {
  if (!span || span.hasAttribute('data-cloze-unbold')) return
  if (!span.hasAttribute('data-pre-bold')) {
    span.setAttribute('data-pre-bold', isClozeFullyBold(span) ? '1' : '0')
  }
  applyDefaultClozeBold(span)
}

function migrateAllClozeBold(root) {
  if (!root?.querySelectorAll) return
  root.querySelectorAll(CLOZE_TAG).forEach(migrateClozeBold)
}

function syncClozeUnboldMarker() {
  const sel = window.getSelection()
  if (!sel?.rangeCount) return
  const anchor = sel.anchorNode
  const el = anchor?.nodeType === 1 ? anchor : anchor?.parentElement
  const cloze = el?.closest?.(CLOZE_TAG)
  if (!cloze || !editBodyRef.value?.contains(cloze)) return
  if (isClozeFullyBold(cloze)) cloze.removeAttribute('data-cloze-unbold')
  else cloze.setAttribute('data-cloze-unbold', '')
}

function normalizeClozeDecorations(root) {
  if (!root?.querySelectorAll) return
  root.querySelectorAll(CLOZE_TAG).forEach(isolateClozeDecorations)
}

function prepareEditHtml(html) {
  const wrap = document.createElement('div')
  wrap.innerHTML = html || ''
  wrap.querySelectorAll(CLOZE_TAG).forEach(revealClozeElement)
  normalizeClozeDecorations(wrap)
  migrateAllClozeBold(wrap)
  cleanupEmptyClozes(wrap)
  consolidateAllClozeGroups(wrap)
  return wrap.innerHTML
}

function clearHiddenClozeColor(node) {
  if (!node?.style) return
  const color = (node.style.color || '').replace(/\s/g, '').toLowerCase()
  const fill = (node.style.webkitTextFillColor || '').replace(/\s/g, '').toLowerCase()
  if (!color || color === 'transparent' || color === 'rgba(0,0,0,0)') node.style.removeProperty('color')
  if (!fill || fill === 'transparent' || fill === 'rgba(0,0,0,0)') node.style.removeProperty('-webkit-text-fill-color')
}

function revealClozeElement(el) {
  if (!el) return
  el.classList.remove('shown')
  clearHiddenClozeColor(el)
  el.querySelectorAll('*').forEach(clearHiddenClozeColor)
}

function revealEditClozes(root) {
  const scope = root || editBodyRef.value || document.querySelector('.editview')
  if (!scope?.querySelectorAll) return
  scope.querySelectorAll(CLOZE_TAG).forEach(revealClozeElement)
  migrateAllClozeBold(scope)
}

function intersectingClozes(range, root) {
  const scope = root || hostOf(range.commonAncestorContainer)
  if (!scope?.querySelectorAll) return []
  return [...scope.querySelectorAll(CLOZE_TAG)].filter(el => {
    try { return range.intersectsNode(el) } catch { return false }
  })
}

function splitRangeByBlocks(range) {
  const startBlock = hostOf(range.startContainer)?.closest(CLOZE_BLOCK_SEL)
  const endBlock = hostOf(range.endContainer)?.closest(CLOZE_BLOCK_SEL)
  if (!startBlock || !endBlock || startBlock === endBlock) return [range]

  const ancestor = range.commonAncestorContainer.nodeType === 1
    ? range.commonAncestorContainer
    : range.commonAncestorContainer.parentElement
  if (!ancestor) return [range]

  const seen = new Set()
  const blocks = []
  for (const b of [startBlock, ...ancestor.querySelectorAll(CLOZE_BLOCK_SEL), endBlock]) {
    if (!b || seen.has(b)) continue
    if (b !== startBlock && b.contains(startBlock)) continue
    if (b !== endBlock && b.contains(endBlock)) continue
    try {
      if (!range.intersectsNode(b)) continue
    } catch {
      continue
    }
    seen.add(b)
    blocks.push(b)
  }
  blocks.sort((a, b) => {
    const pos = a.compareDocumentPosition(b)
    if (pos & Node.DOCUMENT_POSITION_FOLLOWING) return -1
    if (pos & Node.DOCUMENT_POSITION_PRECEDING) return 1
    return 0
  })
  if (blocks.length < 2) return [range]

  const pieces = []
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i]
    const r = document.createRange()
    try {
      if (i === 0) {
        r.setStart(range.startContainer, range.startOffset)
        r.setEnd(b, b.childNodes.length)
      } else if (i === blocks.length - 1) {
        r.setStart(b, 0)
        r.setEnd(range.endContainer, range.endOffset)
      } else {
        r.selectNodeContents(b)
      }
    } catch {
      continue
    }
    if (String(r).replace(/\s+/g, '')) pieces.push(r)
  }
  return pieces.length ? pieces : [range]
}

/** 重叠挖空时把选区扩到相交挖空的完整范围，避免未选中的挖空尾巴被 unwrap 掉 */
function expandRangeToIntersectingClozes(range, root) {
  const expanded = range.cloneRange()
  intersectingClozes(expanded, root).forEach(cloze => {
    try {
      const full = document.createRange()
      full.selectNode(cloze)
      if (expanded.compareBoundaryPoints(Range.START_TO_START, full) > 0) {
        expanded.setStartBefore(cloze)
      }
      if (expanded.compareBoundaryPoints(Range.END_TO_END, full) < 0) {
        expanded.setEndAfter(cloze)
      }
    } catch {}
  })
  return expanded
}

function isSelectionFullyCloze(range) {
  if (!range || range.collapsed) return false
  const block = getBlockForRange(range)
  if (!block) return false
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      try {
        return range.intersectsNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
      } catch {
        return NodeFilter.FILTER_REJECT
      }
    },
  })
  let node
  let hasText = false
  while ((node = walker.nextNode())) {
    if (!normalizeClozeText(node.textContent)) continue
    hasText = true
    if (!node.parentElement?.closest?.(CLOZE_TAG)) return false
  }
  return hasText
}

function removeClozeFromRange(range, root) {
  const startCloze = hostOf(range.startContainer)?.closest?.(CLOZE_TAG)
  const endCloze = hostOf(range.endContainer)?.closest?.(CLOZE_TAG)

  if (startCloze && startCloze === endCloze && (!root || root.contains(startCloze))) {
    if (isFullClozeSelection(range, startCloze)) unwrapCloze(startCloze)
    else unwrapPartialClozeRange(range, startCloze)
    return
  }

  splitRangeAtClozeEdges(range).forEach(piece => {
    const cloze = hostOf(piece.startContainer)?.closest?.(CLOZE_TAG)
    if (!cloze || (root && !root.contains(cloze))) return
    if (isFullClozeSelection(piece, cloze)) unwrapCloze(cloze)
    else unwrapPartialClozeRange(piece, cloze)
  })
}

function mergeClozeRange(range, root) {
  const block = getBlockForRange(range)
  if (!block) return

  const expanded = expandRangeToIntersectingClozes(range, root)
  const meta = rangeToOffsets(expanded, block)
  if (!meta) return

  let current = offsetsToRange(meta)
  if (!current) return

  const hits = intersectingClozes(current, root)
  const inRead = !!hostOf(current.startContainer)?.closest?.('.kb-back')
  const keepShown = hits.some(el => el.classList.contains('shown')) || (inRead && allClozeRevealed.value)
  hits.forEach(unwrapCloze)

  current = offsetsToRange(meta)
  if (!current) return

  const groupId = createClozeGroupId()
  splitRangeByBlocks(current).forEach(r => wrapOneClozeRange(r, groupId, keepShown))
  consolidateClozeGroupInBlock(groupId, block)
}

function finalizeClozeMutation(root, ancestorEl) {
  const scope = root || ancestorEl
  flattenNestedClozes(scope)
  consolidateAllClozeGroups(scope)
  const inEdit = !!(scope?.closest?.('.editview') || (editBodyRef.value && scope && editBodyRef.value.contains(scope)))
  if (inEdit) revealEditClozes(scope)
  cleanupEmptyClozes(scope)
}

function wrapOneClozeRange(range, groupId, shown) {
  if (!String(range).replace(/\s+/g, '')) return
  const preBold = isRangeFullyBold(range)
  const textColor = rangeTextColor(range)
  const span = document.createElement(CLOZE_TAG)
  span.setAttribute('data-pre-bold', preBold ? '1' : '0')
  if (groupId) span.setAttribute('data-cloze-group', groupId)
  if (shown) span.classList.add('shown')
  if (textColor) span.style.color = textColor
  try {
    range.surroundContents(span)
  } catch {
    span.appendChild(range.extractContents())
    range.insertNode(span)
  }
  span.querySelectorAll(CLOZE_TAG).forEach(unwrapCloze)
  isolateClozeDecorations(span)
  if (textColor && !span.style.color) span.style.color = textColor
  applyDefaultClozeBold(span)
}

function applyClozeRange(range, root) {
  const ancestorEl = hostOf(range.commonAncestorContainer)
  if (!hostOf(range.startContainer) || !hostOf(range.endContainer)) return 'none'

  if (isSelectionFullyCloze(range)) {
    removeClozeFromRange(range, root)
    finalizeClozeMutation(root, ancestorEl)
    return 'removed'
  }

  mergeClozeRange(range, root)
  finalizeClozeMutation(root, ancestorEl)
  return 'added'
}

function applyReadCloze() {
  const range = savedReadRange?.cloneRange()
  if (!range) { console.log('[Cloze] savedReadRange is null'); hideClozeBubble(); return }
  const text = String(range).replace(/\s+/g, ' ').trim()
  if (!text) { hideClozeBubble(); return }
  const node = range.commonAncestorContainer
  const el = node.nodeType === 1 ? node : node.parentElement
  if (!el || !el.closest || !el.closest('#docBody') || !el.closest('.kb-back')) {
    hideClozeBubble()
    return
  }
  const result = applyClozeRange(range, el.closest('.kb-back'))
  window.getSelection()?.removeAllRanges()
  emit('flash', result === 'removed' ? '已取消挖空' : '已挖空')
  hideClozeBubble()
  persistReadDoc()
}

// Edit mode
const isEditing = ref(false)
const saving = ref(false)
const editBlocks = ref([])
const editBlockRefs = reactive({})
const isDirty = ref(false)
// 编辑模式切换章节时，pending target chapter id (unsaved dialog 确认后继续)
let pendingEditChapter = null
const editSnapshot = ref('')
const isBatch = ref(false)
const batchMode = ref(null)
const brushOn = ref(false)
let brushStroke = false
let brushPaintLock = false
const aiLock = ref(false)
const aiBusy = ref(false)
const editViewRef = ref(null)
const editBodyRef = ref(null)
const ePageRef = ref(null)

// Etool state
const etOpen = reactive({ style: false, color: false, block: false })
const etStates = reactive({ bold: false, italic: false, underline: false, strike: false, ol: false, ul: false, cloze: false })
const etStyle = ref('p')
const etStyleLabel = computed(() => {
  const names = { p: '正文', h1: 'H1', h2: 'H2', h3: 'H3' }
  return names[etStyle.value] || '正文'
})

// Selection toolbar
const selbarVisible = ref(false)
const selbarBelow = ref(false)
const selbarStyle = ref({})
const selbarRef = ref(null)
const selOpen = reactive({ style: false, color: false })
const selStates = reactive({ bold: false, italic: false, underline: false, strike: false })

// Drag-and-drop for edit blocks (mouse-based)
const dragOverIdx = ref(-1)
let dragFromIdx = -1
let dragStartY = 0
let dragEl = null
let dragClone = null

function onMouseDown(i, event) {
  event.preventDefault()
  event.stopPropagation()
  dragFromIdx = i
  dragStartY = event.clientY
  dragEl = event.currentTarget.closest('.eblk')
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

let dragMoved = false

function onMouseMove(event) {
  if (!dragEl) return
  // 移动至少 5px 才启动拖拽
  if (!dragMoved && Math.abs(event.clientY - dragStartY) < 5) return
  if (!dragMoved) {
    dragMoved = true
    // 创建拖拽克隆
    dragClone = dragEl.cloneNode(true)
    dragClone.style.position = 'fixed'
    dragClone.style.pointerEvents = 'none'
    dragClone.style.opacity = '0.8'
    dragClone.style.zIndex = '9999'
    dragClone.style.width = dragEl.offsetWidth + 'px'
    dragClone.style.left = dragEl.getBoundingClientRect().left + 'px'
    dragClone.style.top = event.clientY + 'px'
    document.body.appendChild(dragClone)
    dragEl.style.opacity = '0.3'
  }
  if (dragClone) {
    dragClone.style.top = event.clientY + 'px'
  }
  // 计算当前悬停位置
  const blocks = document.querySelectorAll('.eblk')
  let targetIdx = -1
  blocks.forEach((block, idx) => {
    const rect = block.getBoundingClientRect()
    if (event.clientY >= rect.top && event.clientY <= rect.bottom) {
      targetIdx = idx
    }
  })
  dragOverIdx.value = targetIdx
}

function onMouseUp() {
  if (dragMoved && dragClone) {
    document.body.removeChild(dragClone)
    dragClone = null
  }
  if (dragEl) dragEl.style.opacity = ''
  if (dragMoved && dragFromIdx >= 0 && dragOverIdx.value >= 0 && dragFromIdx !== dragOverIdx.value) {
    const item = editBlocks.value.splice(dragFromIdx, 1)[0]
    // 调整目标索引：删除后后续项前移一位
    const insertAt = dragOverIdx.value > dragFromIdx ? dragOverIdx.value - 1 : dragOverIdx.value
    editBlocks.value.splice(insertAt, 0, item)
  }
  dragFromIdx = -1
  dragOverIdx.value = -1
  dragEl = null
  dragMoved = false
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
}
const selStyle = ref('p')
const selInCloze = ref(false)
let savedRange = null
let toolbarRange = null
let selbarInteracting = false
let nextBlockId = 1

function enterEdit(forceChapterId) {
  if (isEditing.value) return
  try {
    enterEditUnsafe(forceChapterId)
  } catch (err) {
    console.error('[enterEdit] failed', err)
    isEditing.value = false
    flash('进入编辑失败')
  }
}

function enterEditUnsafe(forceChapterId) {
  // 防抖：@click 直接绑方法时 Vue 会把 PointerEvent 作为首参传入，它不是章节 id；
  // 若不滤掉，findIndex 找不到章节 → curStart/curEnd 保持全量 → 把已加载的所有章节都带入编辑
  if (forceChapterId != null && typeof forceChapterId !== 'string' && typeof forceChapterId !== 'number') {
    forceChapterId = null
  }
  captureClozeRevealState()
  // DynamicScroller 的 ref 是组件实例，必须走 $el，否则 querySelectorAll 会直接抛错
  const dPage = scrollEl.value
  const visibleOrigIndices = new Set()
  if (dPage) {
    // 虚拟列表的卡片是 transform 定位的，offsetTop 只反映卡片内部的偏移、与滚动位置无关；
    // 必须用 getBoundingClientRect 与滚动容器视口直接比较，才能拿到真正在视口内的块。
    // （目录跳到深处后 scrollTop 很大，旧写法一个块都测不出，编辑范围会选错章节）
    const scrollerRect = dPage.getBoundingClientRect()
    Array.from(dPage.querySelectorAll('.d-sec')).forEach(el => {
      const rect = el.getBoundingClientRect()
      if (rect.bottom > scrollerRect.top + 1 && rect.top < scrollerRect.bottom - 1) {
        const idx = parseInt(el.dataset.index)
        if (!isNaN(idx)) visibleOrigIndices.add(idx)
      }
    })
  }

  // 确定编辑范围：只编辑当前这一章（以视口内第一个可见分块所在章为准）
  let curStart = 0
  let curEnd = sections.value.length
  if (forceChapterId != null) {
    // 目录切换章节时传入章节 ID，跳过视口检测，直接定位到该章节
    const chIdx = chapterList.value.findIndex(ch => String(ch.id) === String(forceChapterId))
    if (chIdx >= 0) {
      // 找到该章节的第一个内容块（跳过 chapterTitle）
      const firstSecIdx = sections.value.findIndex(s => s._chapterIdx === chIdx && s.type !== 'chapterTitle')
      if (firstSecIdx >= 0) {
        curStart = firstSecIdx
        // 向后找下一章标题作为结束
        for (let i = firstSecIdx + 1; i < sections.value.length; i++) {
          if (sections.value[i].type === 'chapterTitle') { curEnd = i; break }
        }
      }
    }
  } else if (visibleOrigIndices.size > 0) {
    const anchor = Math.min(...visibleOrigIndices)
    const anchorSec = sections.value[anchor]
    if (anchorSec) {
      // 章节起点：锚点本身是本章标题时从其开始，否则向前找本章标题
      let startIdx = anchor
      if (anchorSec.type !== 'chapterTitle') {
        for (let i = anchor - 1; i >= 0; i--) {
          if (sections.value[i].type === 'chapterTitle') { startIdx = i; break }
        }
      }
      // 章节结束：向后找下一章标题
      let endIdx = sections.value.length
      for (let i = startIdx + 1; i < sections.value.length; i++) {
        if (sections.value[i].type === 'chapterTitle') { endIdx = i; break }
      }
      curStart = startIdx
      curEnd = endIdx
    }
  }

  // 只编辑锚点所在的这一章
  const targetSections = (forceChapterId != null || visibleOrigIndices.size > 0)
    ? sections.value.slice(curStart, curEnd).filter(sec => sec.type !== 'chapterTitle')
    : sections.value.filter(sec => sec.type !== 'chapterTitle')

  isEditing.value = true
  isDirty.value = false
  isBatch.value = false
  batchMode.value = null
  brushOn.value = false
  // Reset block refs
  Object.keys(editBlockRefs).forEach(k => delete editBlockRefs[k])
  editBlocks.value = targetSections.map(sec => ({
    id: nextBlockId++,
    html: (() => {
      const html = renderMathInRichText(sec.content)
      const hasDollar = sec.content.includes('$')
      const hasMathSpan = html.includes('class="math"')
      console.log('[formula] enterEdit block', { hasDollar, hasMathSpan, isTable: !!sec.isTable, contentLen: sec.content.length, htmlLen: html.length })
      return prepareEditHtml(html)
    })(),
    chapterId: sec.chapterId,
    picked: false,
    splitOpen: false,
    // 表格块：编辑源是 markdown txt（vditor），不是渲染 HTML
    isTable: !!sec.isTable,
    txt: sec.txt || ''
  }))
  editSnapshot.value = getEditSnapshot()
  resetEditHistory()
  nextTick(() => {
    hideSelbar()
    syncEtool()
    initTableVditors()
    revealEditClozes()
    // 检查 DOM 中 .math 元素的数量
    const firstEblkTxt = document.querySelector('.eblk-txt')
    if (firstEblkTxt) {
      console.log('[formula] DOM after render - math count:', firstEblkTxt.querySelectorAll('.math').length, 'innerHTML has math:', firstEblkTxt.innerHTML.includes('class="math"'))
      // 检查 eblk-txt 的 contenteditable 属性
      console.log('[formula] contenteditable:', firstEblkTxt.getAttribute('contenteditable'))
    }
  })
}

function getEditSnapshot() {
  return editBlocks.value.map(b => (b.isTable ? 'TABLE::' + (b.txt || '') : b.html)).join('\n---\n')
}

function markDirty() {
  // 表格块的内容在 vditor 内部 DOM 里：先把 getValue() 同步回块的 txt，再比较快照。
  // vditor 的 input 事件会冒泡到 .e-inner（onBlockInput）与这里，二者都走这个同步
  editBlocks.value.forEach(b => {
    if (b.isTable) {
      const v = vditorInsts[b.id]
      if (v) b.txt = v.getValue()
    }
  })
  isDirty.value = getEditSnapshot() !== editSnapshot.value
}

function onBlockInput(i, event) {
  const blk = editBlocks.value[i]
  if (blk.isTable) return  // 表格块由 vditor 管理，markDirty 已同步
  const el = editBlockRefs[i]
  if (el) blk.html = el.innerHTML
  markDirty()
}

// ---- 表格块 vditor 实例管理 ----
// 编辑源是 markdown txt（后端原本的管道格式），vditor 加载/编辑/取回都走 markdown，
// 不再需要 tableToMarkdown 反序列化与配套的标点转义逻辑
const vditorInsts = {}

function initTableVditors() {
  editBlocks.value.forEach(blk => {
    if (!blk.isTable || vditorInsts[blk.id] || !document.getElementById('vtbl-' + blk.id)) return
    const v = new Vditor('vtbl-' + blk.id, {
      mode: 'ir',                    // 即时渲染：$...$ 公式实时 KaTeX，表格 markdown 源码可见
      value: blk.txt || '',
      theme: 'classic',
      cache: { enable: false },
      // Lute 原生把 $...$ 渲染为公式（$5 价格有防误判），$$...$$ 反而错乱；
      // 所以存储协议统一单美元，旧 $$ 数据在阅读侧渲染层仍兼容
      math: { engine: 'KaTeX' },
      toolbar: ['undo', 'redo', '|', 'table'],
      after: () => {
        // vditor 首次 setValue 会规范化源码（<br> 表达、空行等），以规范化结果对齐快照，
        // 避免一进编辑就被标记为已修改；此后用户的每次输入由 input 监听同步回 blk.txt
        blk.txt = v.getValue()
        editSnapshot.value = getEditSnapshot()
        isDirty.value = false
        // 直接监听实例容器 input，不依赖冒泡到 .e-inner：键盘输入、撤销重做、
        // 工具栏插入表格等改动全部兜底同步，保证保存提交的是最新值
        const editorEl = v.vditor && v.vditor.element
        if (editorEl) {
          editorEl.addEventListener('input', () => {
            blk.txt = v.getValue()
            markDirty()
          })
        }
      }
    })
    vditorInsts[blk.id] = v
    // 诊断入口：浏览器 Console 里跑 Object.values(window.__vditorInsts).map(v => v.getValue())
    // 拿 vditor 实际输出 markdown，便于和阅读侧渲染结果对比
    window.__vditorInsts = vditorInsts
  })
}

function destroyTableVditors() {
  Object.keys(vditorInsts).forEach(id => {
    try { vditorInsts[id].destroy() } catch (e) { /* 实例可能已释放 */ }
    delete vditorInsts[id]
  })
}

// 选区是否落在 vditor 内部：选择工具栏（样式/挖空/颜色）作用于自研 DOM，
// 对 vditor 的内容施 execCommand 会破坏其结构，必须拦截
function selInVditor() {
  const sel = window.getSelection()
  if (!sel || !sel.anchorNode) return false
  const n = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement
  return !!(n && n.closest && n.closest('.vditor'))
}

watch(isEditing, v => {
  if (!v) {
    hideSelbar()
    closeEtoolPops()
    closeMathEditor()
    destroyTableVditors()
    resetEditHistory()
    window.getSelection()?.removeAllRanges()
  }
})

async function saveEdit(options = {}) {
  const { keepSaving = false } = options
  saving.value = true
  // Sync all blocks from DOM
  editBlocks.value.forEach((blk, i) => {
    const el = editBlockRefs[i]
    if (el) blk.html = el.innerHTML
  })
  editSnapshot.value = getEditSnapshot()
  isDirty.value = false
  // 生成并保存阅读模式 HTML，每个块按内容区分类型：纯表格块为 TABLE，纯图片块为 IMG，其余为 TXT
  syncToSections()
  // 调用新增或全量更新接口
  try {
    // 图片块先上传拿到 ResourceDataBean（objId/objKey），再作为独立 IMG 块提交
    const data = []
    for (let i = 0; i < editBlocks.value.length; i++) {
      const blk = editBlocks.value[i]
      // 表格块：vditor 编辑的就是 markdown 原文，直接提交，不经过 DOM 序列化
      if (blk.isTable) {
        data.push({ bookDataType: 'TABLE', title: `表格块 ${i + 1}`, txt: blk.txt || '' })
        continue
      }
      const temp = document.createElement('div')
      temp.innerHTML = blk.html
      const img = temp.querySelector('img')
      const isImg = img && !(temp.textContent || '').trim()
      // 纯表格块：<table> 之外无其他内容（md-block 包裹层忽略），txt 保持 markdown 管道格式
      const tableEl = temp.querySelector('table')
      let isTable = false
      if (tableEl) {
        const stripped = temp.cloneNode(true)
        stripped.querySelectorAll('table').forEach(t => t.remove())
        isTable = !stripped.textContent.trim() && !stripped.querySelector('img')
      }
      if (isTable) {
        data.push({ bookDataType: 'TABLE', title: `表格块 ${i + 1}`, txt: tableToMarkdown(tableEl) })
      } else if (isImg) {
        const src = img.getAttribute('src') || ''
        let resourceDataBean = null
        if (src.startsWith('data:image/')) {
          resourceDataBean = await uploadImageDataUrl(src)
        }
        data.push({ bookDataType: 'IMG', title: `图片 ${i + 1}`, resourceDataBean })
      } else {
        // TXT 分支：先把 KaTeX 渲染的公式还原为 $$源码$$，保证 richTxt/txt 不包含渲染 HTML
        restoreMathSpans(temp)
        data.push({
          bookDataType: 'TXT',
          title: `文本块 ${i + 1}`,
          // 用还原公式后的 temp.innerHTML（与 txt 同源），避免 KaTeX 渲染 HTML 落库
          richTxt: temp.innerHTML,
          txt: temp.textContent || ''
        })
      }
    }
    // 入参：id = 当前编辑的章节 id（新增书籍时为空，服务端走新增）；bookId 不传
    const chapterIds = [...new Set(editBlocks.value.map(b => b.chapterId).filter(Boolean))]
    const chapterId = chapterIds[0] || null
    const res = await bookApi.saveBook({
      id: chapterId || undefined,
      title: props.doc?.title || '',
      data
    })
    if (res.code !== 0) {
      emit('flash', res.msg || '保存失败')
      return
    }
    // 新增成功后，把服务端返回的书 id（parentBookId，即书籍列表中的 id）
    // 回传父组件替换本地临时 id
    if (props.isNewDoc && res.data && res.data.parentBookId) {
      emit('save-book', { from: props.currentDoc, id: res.data.parentBookId })
    }
    emit('flash', '已保存')
    // 编辑保存成功后，只重新加载当前章节的数据
    if (chapterId) {
      try {
        const detail = await bookApi.getDetail({ id: chapterId })
        if (detail.code === 0 && detail.data && Array.isArray(detail.data.bookDataList)) {
          // 保留原章节标题，重建该章节的内容块（IMG 块异步补 URL）
          const oldTitle = sections.value.find(s => s.type === 'chapterTitle' && s.chapterId === chapterId)?.text || ''
          const newItems = await compileChapterItems(detail.data.bookDataList, chapterId, oldTitle)
          // 更新缓存
          const chapterIdx = chapterList.value.findIndex(ch => ch.id === chapterId)
          if (chapterIdx >= 0) {
            chapterList.value[chapterIdx]._content = newItems
            rebuildSections()
          }
        }
      } catch (err) {
        console.warn('重新加载章节失败', err)
      }
    }
  } catch (err) {
    console.warn('保存失败', err)
    emit('flash', '网络异常，请稍后重试')
  } finally {
    if (!keepSaving) saving.value = false
  }
}

async function doneEdit() {
  if (saving.value) return
  saving.value = true
  try {
    await saveEdit({ keepSaving: true })
    isEditing.value = false
    isBatch.value = false
    batchMode.value = null
    brushOn.value = false
    aiLock.value = false
  } finally {
    saving.value = false
  }
}

function requestLeaveEdit() {
  if (isDirty.value) {
    pendingEditChapter = null // 退出编辑（非切换章节），清除待切换
    emit('open-unsaved')
    return
  }
  isEditing.value = false
  isBatch.value = false
  batchMode.value = null
}

// 未保存弹框的回调（由 App.vue 通过 defineExpose 调用）
function cancelEdit() {
  // 有 pending 章节切换 → 直接跳转，不退出编辑（避免阅读视图闪一下）
  if (pendingEditChapter) {
    const chId = pendingEditChapter
    pendingEditChapter = null
    isBatch.value = false
    batchMode.value = null
    brushOn.value = false
    aiLock.value = false
    nextTick(() => switchEditChapter(chId))
    return
  }
  // 不保存：直接退出编辑；阅读视图基于 sections 渲染不受影响，
  // 下次进入编辑时 editBlocks 会从 sections 重建，未保存的修改即被丢弃
  isEditing.value = false
  isBatch.value = false
  batchMode.value = null
  brushOn.value = false
  aiLock.value = false
}

async function confirmSave() {
  // 保存：与「完成」一致，保存后端后退出编辑
  await doneEdit()
  // 有 pending 章节切换 → 跳转后重新进入编辑
  if (pendingEditChapter) {
    const chId = pendingEditChapter
    pendingEditChapter = null
    // doneEdit 已设置 isEditing = false，立即重新进入编辑（同一 tick 内 Vue 不会渲染中间态）
    isEditing.value = true
    await switchEditChapter(chId)
  }
}

defineExpose({ cancelEdit, confirmSave, enterEdit })

// syncToSections: convert edit blocks to reading sections with cloze spans
function syncToSections() {
  // 保留 chapterTitle 标记，只替换普通块
  const newSecs = editBlocks.value.map((blk, i) => {
    // 表格块：直接用 vditor 的 markdown 渲染阅读内容（与后端回读展示同一条路径）
    if (blk.isTable) {
      return {
        qtitle: `表格块 ${i + 1}`,
        content: buildBlockContent({ dataBaseBean: { bookDataType: 'TABLE', txt: blk.txt || '' } }),
        flipped: false,
        minHeight: 0,
        editingTitle: false,
        aiGenerated: false,
        aiGenerating: false,
        compactFlip: false
      }
    }
    const temp = document.createElement('div')
    temp.innerHTML = editClozeToRead(blk.html)
    const h = temp.querySelector('h1, h2, h3')
    const title = h ? (h.textContent || '').replace(/^[一二三四五六七八九十]+、/, '') : `文本块 ${i + 1}`
    return {
      qtitle: clampBlockTitle(title),
      content: renderMathInRichText(temp.innerHTML),
      flipped: false,
      minHeight: 0,
      editingTitle: false,
      aiGenerated: false,
      aiGenerating: false,
      compactFlip: false
    }
  })
  // 合并：保留原有的 chapterTitle，替换普通块
  let editIdx = 0
  const merged = sections.value.map(s => {
    if (s.type === 'chapterTitle') return s
    return newSecs[editIdx++] || s
  })
  sections.value = merged
  // Also save back to DOCS
  const combinedHtml = sections.value.filter(s => s.type !== 'chapterTitle').map(s => s.content).join('')
  emit('save-doc', wrapInSections(combinedHtml, sections.value))
}

function wrapInSections(html, secs) {
  return secs.filter(s => s.type !== 'chapterTitle').map((s, i) => {
    const br = (i > 0 && i % 2 === 0) ? `<div class="pagebreak"><span>第${Math.floor(i / 2 + 1)}页</span></div>` : ''
    return br + `<section class="d-sec">${s.content}</section>`
  }).join('')
}

// ===== Edit toolbar actions =====
function toggleEtool(name) {
  if (etOpen[name]) {
    etOpen[name] = false
  } else {
    Object.keys(etOpen).forEach(k => etOpen[k] = false)
    etOpen[name] = true
  }
}

function applyFormat(cmd, value) {
  if (cmd === 'underline' || cmd === 'strikeThrough') {
    toggleInlineDecoration(cmd, false)
    return
  }
  pushEditHistory()
  restoreRange()
  if (cmd === 'foreColor') document.execCommand('styleWithCSS', false, true)
  if (cmd === 'bold') toggleUserBold()
  else document.execCommand(cmd, false, value)
  if (window.getSelection().rangeCount) refreshSavedRange()
  syncActiveBlockHtml()
  syncEtool()
  closeEtoolPops()
}

function toggleUserBold() {
  const range = expandRangeForBold()
  if (!range) return
  const heading = headingOf(range.startContainer)
  const active = isUserBoldActive()
  const parts = splitRangeForDeco(range)
  if (active) {
    parts.forEach(unwrapUserBoldInRange)
    if (heading) {
      wrapDecoRanges(splitRangeForDeco(liveBoldRange(range)), 'SPAN').forEach(el => {
        el.setAttribute('data-user-unbold', '')
        el.style.fontWeight = '400'
      })
    }
  } else {
    parts.forEach(unwrapUserUnboldInRange)
    if (!heading) wrapDecoRanges(splitRangeForDeco(liveBoldRange(range)), 'B')
  }
  normalizeDecoInClozes(liveBoldRange(range))
  syncClozeUnboldMarker()
}

function syncEtool() {
  const map = { bold: 'bold', italic: 'italic', underline: 'underline', strike: 'strikeThrough', ol: 'insertOrderedList', ul: 'insertUnorderedList' }
  Object.keys(map).forEach(act => {
    if (act === 'underline') etStates.underline = inlineDecoActive('underline')
    else if (act === 'strike') etStates.strike = inlineDecoActive('strikeThrough')
    else if (act === 'bold') etStates.bold = isUserBoldActive()
    else etStates[act] = document.queryCommandState(map[act])
  })
  const block = (document.queryCommandValue('formatBlock') || 'p').replace(/[<>]/g, '').toLowerCase()
  etStyle.value = (block === 'div' || !block) ? 'p' : block
}

function closeEtoolPops() {
  Object.keys(etOpen).forEach(k => etOpen[k] = false)
}

function etoolPopOpen() {
  return Object.values(etOpen).some(Boolean)
}

function closeEtoolPopsOutside(e) {
  if (!isEditing.value || !etoolPopOpen()) return
  const t = e.target
  if (t?.closest?.('.etb.open') || t?.closest?.('.etb-pop')) return
  closeEtoolPops()
}

function toggleCloze() {
  if (savedRange) toolbarRange = savedRange.cloneRange()
  saveToolbarSelMeta()
  restoreRange()
  const sel = window.getSelection()
  if (!sel?.rangeCount || sel.isCollapsed) {
    emit('flash', '请先选中要挖空的文字')
    return
  }
  pushEditHistory()
  const range = sel.getRangeAt(0).cloneRange()
  const result = applyClozeRange(range, editBodyRef.value)
  emit('flash', result === 'removed' ? '已取消挖空' : '已挖空')
  finishFormatAction(selbarVisible.value)
}

function toggleBrush() {
  setBrushOn(!brushOn.value)
  emit('flash', brushOn.value ? '挖空刷已开启，拖选文字即可挖空或取消挖空' : '挖空刷已关闭')
}

function setBrushOn(on) {
  brushOn.value = !!on
  brushStroke = false
  hideSelbar()
  if (!brushOn.value) return
  window.getSelection()?.removeAllRanges()
  savedRange = null
  toolbarRange = null
  toolbarSelMeta = null
}

function applyBrushCloze() {
  if (!brushOn.value || brushPaintLock) return
  if (selInVditor()) return
  const sel = window.getSelection()
  if (!sel?.rangeCount || sel.isCollapsed) return
  const node = sel.anchorNode
  const el = node && (node.nodeType === 1 ? node : node.parentElement)
  if (!el?.closest?.('#editBody')) return
  if (!String(sel).replace(/\s+/g, ' ').trim()) return
  brushPaintLock = true
  try {
    pushEditHistory()
    const range = sel.getRangeAt(0).cloneRange()
    const result = applyClozeRange(range, editBodyRef.value)
    emit('flash', result === 'removed' ? '已取消挖空' : '已挖空')
    finishFormatAction(false)
    hideSelbar()
  } finally {
    queueMicrotask(() => { brushPaintLock = false })
  }
}

const EDIT_HISTORY_LIMIT = 20
let editUndoStack = []
let editRedoStack = []
let editHistoryLocked = false
let editTypingHistOpen = false
let editTypingHistTimer = 0
const canEditUndo = ref(false)
const canEditRedo = ref(false)

function syncEditHistoryButtons() {
  canEditUndo.value = editUndoStack.length > 0
  canEditRedo.value = editRedoStack.length > 0
}

function resetEditHistory() {
  editUndoStack = []
  editRedoStack = []
  editHistoryLocked = false
  editTypingHistOpen = false
  clearTimeout(editTypingHistTimer)
  syncEditHistoryButtons()
}

function syncLiveEditHtml() {
  editBlocks.value.forEach((blk, i) => {
    if (blk.isTable) {
      const v = vditorInsts[blk.id]
      if (v) blk.txt = v.getValue()
      return
    }
    const el = editBlockRefs[i]
    if (el) blk.html = el.innerHTML
  })
}

function cloneEditHistoryState() {
  syncLiveEditHtml()
  return {
    nextBlockId,
    blocks: editBlocks.value.map(b => ({
      id: b.id,
      html: b.html,
      txt: b.txt,
      isTable: !!b.isTable,
      chapterId: b.chapterId,
      picked: !!b.picked,
    })),
  }
}

function editHistoryEqual(a, b) {
  if (!a || !b || a.blocks.length !== b.blocks.length) return false
  return a.blocks.every((blk, i) => {
    const other = b.blocks[i]
    return blk.id === other.id && blk.html === other.html && blk.txt === other.txt && blk.isTable === other.isTable
  })
}

function pushEditHistory() {
  if (editHistoryLocked || !isEditing.value) return
  editTypingHistOpen = false
  clearTimeout(editTypingHistTimer)
  const state = cloneEditHistoryState()
  const last = editUndoStack[editUndoStack.length - 1]
  if (last && editHistoryEqual(last, state)) return
  editUndoStack.push(state)
  if (editUndoStack.length > EDIT_HISTORY_LIMIT) editUndoStack.shift()
  editRedoStack = []
  syncEditHistoryButtons()
}

function onBlockBeforeInput() {
  if (editHistoryLocked || !isEditing.value) return
  if (!editTypingHistOpen) {
    pushEditHistory()
    editTypingHistOpen = true
  }
  clearTimeout(editTypingHistTimer)
  editTypingHistTimer = window.setTimeout(() => { editTypingHistOpen = false }, 600)
}

function applyEditHistoryState(state) {
  if (!state) return
  editHistoryLocked = true
  hideSelbar()
  destroyTableVditors()
  nextBlockId = state.nextBlockId || nextBlockId
  editBlocks.value = state.blocks.map(b => ({
    id: b.id,
    html: b.html,
    txt: b.txt,
    isTable: b.isTable,
    chapterId: b.chapterId,
    picked: b.picked,
    splitOpen: false,
  }))
  nextTick(() => {
    editBlocks.value.forEach((blk, i) => {
      if (blk.isTable) return
      const el = editBlockRefs[i]
      if (el) {
        el.innerHTML = prepareEditHtml(blk.html)
        el.__init = true
      }
    })
    initTableVditors()
    revealEditClozes()
    markDirty()
    syncEtool()
    editHistoryLocked = false
  })
}

function applyEditUndo() {
  if (!editUndoStack.length) {
    emit('flash', '没有可撤销的操作')
    return
  }
  const current = cloneEditHistoryState()
  const prev = editUndoStack.pop()
  editRedoStack.push(current)
  if (editRedoStack.length > EDIT_HISTORY_LIMIT) editRedoStack.shift()
  applyEditHistoryState(prev)
  syncEditHistoryButtons()
}

function applyEditRedo() {
  if (!editRedoStack.length) {
    emit('flash', '没有可重做的操作')
    return
  }
  const current = cloneEditHistoryState()
  const next = editRedoStack.pop()
  editUndoStack.push(current)
  if (editUndoStack.length > EDIT_HISTORY_LIMIT) editUndoStack.shift()
  applyEditHistoryState(next)
  syncEditHistoryButtons()
}

function undo() {
  applyEditUndo()
}

function redo() {
  applyEditRedo()
}

// Batch operations
const pickedBlocks = computed(() => editBlocks.value.filter(b => b.picked))

function enterBatchMode(mode) {
  closeEtoolPops()
  if (isBatch.value && batchMode.value === mode) {
    exitBatchMode()
    return
  }
  setBrushOn(false)
  isBatch.value = true
  batchMode.value = mode
  hideSelbar()
  closeEtoolPops()
}

function toggleBatch() {
  enterBatchMode('merge')
}

function exitBatchMode() {
  isBatch.value = false
  batchMode.value = null
  editBlocks.value.forEach(b => b.picked = false)
  closeEtoolPops()
}

function syncBatch() {
  const n = pickedBlocks.value.length
  const mergeBtn = document.querySelector('#btnMerge')
  if (mergeBtn) mergeBtn.textContent = `合并（${n}）`
}

function blockMergeHtml(html) {
  const wrap = document.createElement('div')
  wrap.innerHTML = html || ''
  const blockTags = /^(P|DIV|H1|H2|H3|H4|H5|H6|UL|OL|TABLE|BLOCKQUOTE|PRE|FIGURE|SECTION|HR)$/
  const out = []
  let inline = ''
  const flushInline = () => {
    const text = inline.replace(/&nbsp;/g, ' ').replace(/<br\s*\/?>/gi, '').trim()
    if (text) out.push(`<p>${inline}</p>`)
    inline = ''
  }
  ;[...wrap.childNodes].forEach(n => {
    if (n.nodeType === 1 && blockTags.test(n.tagName)) {
      flushInline()
      out.push(n.outerHTML)
    } else {
      inline += n.outerHTML || n.textContent || ''
    }
  })
  flushInline()
  return out.join('') || '<p><br></p>'
}

function mergeBlocks() {
  const list = pickedBlocks.value
  if (list.length < 2) return
  if (list.some(b => b.isTable)) { emit('flash', '表格块暂不支持合并'); return }
  pushEditHistory()
  syncLiveEditHtml()
  const first = list[0]
  first.html = list.map(b => blockMergeHtml(b.html)).join('')
  const ids = list.slice(1).map(b => b.id)
  editBlocks.value = editBlocks.value.filter(b => !ids.includes(b.id))
  first.picked = false
  if (!editBlocks.value.length) {
    editBlocks.value.push(first)
  }
  nextTick(() => {
    const newIdx = editBlocks.value.indexOf(first)
    const el = newIdx >= 0 ? editBlockRefs[newIdx] : null
    if (el) {
      el.innerHTML = prepareEditHtml(first.html)
      el.__init = true
    }
    Object.keys(editBlockRefs).forEach(k => {
      if (k >= editBlocks.value.length) delete editBlockRefs[k]
    })
  })
  emit('flash', `已合并 ${list.length} 个分块`)
  exitBatchMode()
}

function deleteBlocks() {
  const list = pickedBlocks.value
  if (!list.length) return
  pushEditHistory()
  const ids = list.map(b => b.id)
  ids.forEach(id => {
    if (vditorInsts[id]) {
      try { vditorInsts[id].destroy() } catch (e) { /* 实例可能已释放 */ }
      delete vditorInsts[id]
    }
  })
  editBlocks.value = editBlocks.value.filter(b => !ids.includes(b.id))
  if (!editBlocks.value.length) {
    editBlocks.value.push({ id: nextBlockId++, html: '<p><br></p>', picked: false, splitOpen: false })
  }
  emit('flash', `已删除 ${list.length} 个分块`)
  exitBatchMode()
}

function deleteBlockAt(i) {
  if (i < 0 || i >= editBlocks.value.length) return
  closeSplitPops()
  pushEditHistory()
  const blk = editBlocks.value[i]
  if (blk?.isTable && vditorInsts[blk.id]) {
    try { vditorInsts[blk.id].destroy() } catch (e) { /* 实例可能已释放 */ }
    delete vditorInsts[blk.id]
  }
  editBlocks.value.splice(i, 1)
  if (!editBlocks.value.length) {
    editBlocks.value.push({ id: nextBlockId++, html: '<p><br></p>', picked: false, splitOpen: false })
  }
  Object.keys(editBlockRefs).forEach(k => {
    if (Number(k) >= editBlocks.value.length) delete editBlockRefs[k]
  })
  markDirty()
  emit('flash', '已删除分块')
}

// Block split
function toggleSplit(i) {
  editBlocks.value[i].splitOpen = !editBlocks.value[i].splitOpen
}

function closeSplitPops() {
  editBlocks.value.forEach(b => b.splitOpen = false)
}

function applyBlockSplit(i, mode) {
  const blk = editBlocks.value[i]
  if (blk.isTable) { emit('flash', '表格块暂不支持按行拆分'); return }
  const pieces = splitBlockPieces(blk.html, mode)
  if (pieces.length < 2) { emit('flash', '无可拆分内容'); return }
  pushEditHistory()
  blk.html = pieces[0]
  const newBlocks = pieces.slice(1).map(html => ({
    id: nextBlockId++,
    html,
    picked: false,
    splitOpen: false
  }))
  editBlocks.value.splice(i + 1, 0, ...newBlocks)
  closeSplitPops()
  // 清除 __init 标记，让 DOM 更新拆分后的内容（原块只剩第一段）
  const el = editBlockRefs[i]
  if (el) delete el.__init
  emit('flash', `已拆成 ${pieces.length} 个分块`)
}

function splitBlockPieces(html, mode) {
  const div = document.createElement('div')
  div.innerHTML = html
  if (mode === 'period') {
    const parts = html.split(/(?<=。)/)
    return parts.filter(p => p.replace(/<[^>]+>/g, '').trim())
  }
  if (mode === 'blank') {
    const parts = html.split(/<p(?:\s[^>]*)?>\s*(?:<br\s*\/?>)?\s*<\/p>/i)
    if (parts.length < 2) return [html]
    return parts.map(p => p.trim()).filter(p => p.replace(/<[^>]+>/g, '').trim())
  }
  // line mode — DOM-based, 保留元素结构，<br> 作为行分隔符
  const pieces = []
  let buf = document.createDocumentFragment()
  function flush() {
    if (buf.textContent.trim()) {
      const wrap = document.createElement('div')
      wrap.appendChild(buf)
      pieces.push(wrap.innerHTML)
      buf = document.createDocumentFragment()
    }
  }
  function walkNodes(nodes) {
    for (const node of nodes) {
      if (node.nodeType === 3) { // text
        const lines = node.nodeValue.split('\n')
        lines.forEach((line, i) => {
          if (i > 0) flush()
          if (line) buf.appendChild(document.createTextNode(line))
        })
      } else if (node.nodeType === 1) {
        if (node.tagName === 'BR') {
          flush()
        } else if (node.querySelector('br')) {
          // 元素内有 <br>，先 flush 之前累积的内容
          flush()
          // 在元素内部按 <br> 拆分，保留元素标签
          const inner = document.createElement(node.tagName)
          for (const attr of node.attributes) inner.setAttribute(attr.name, attr.value)
          let cur = document.createDocumentFragment()
          function flushInner() {
            if (cur.textContent.trim()) {
              const el = inner.cloneNode(false)
              el.appendChild(cur)
              buf.appendChild(el)
              cur = document.createDocumentFragment()
              flush() // 每个 <br> 分段后都 flush 到 pieces
            }
          }
          for (const child of node.childNodes) {
            if (child.nodeType === 3) {
              cur.appendChild(child.cloneNode(true))
            } else if (child.nodeType === 1 && child.tagName === 'BR') {
              flushInner()
            } else {
              cur.appendChild(child.cloneNode(true))
            }
          }
          flushInner()
        } else {
          buf.appendChild(node.cloneNode(true))
        }
      }
    }
  }
  walkNodes(div.childNodes)
  flush()
  // 如果没有 <br> 且有多子元素，按子元素拆分（兼容原 fallback 逻辑）
  if (pieces.length < 2) {
    const kids = Array.from(div.childNodes).filter(n => {
      if (n.nodeType === 3) return n.nodeValue.trim()
      if (n.nodeType === 1) return n.tagName !== 'BR'
      return false
    })
    if (kids.length >= 2) {
      return kids.map(n => n.nodeType === 3 ? n.nodeValue : n.outerHTML)
    }
    return [html]
  }
  return pieces
}

function newBlock() {
  closeEtoolPops()
  pushEditHistory()
  const blk = { id: nextBlockId++, html: '<p><br></p>', picked: false, splitOpen: false }
  // 找到光标所在的分块，插入在其后
  let insertIdx = editBlocks.value.length - 1
  for (let i = 0; i < editBlocks.value.length; i++) {
    const el = editBlockRefs[i]
    if (el && el === document.activeElement) {
      insertIdx = i
      break
    }
  }
  editBlocks.value.splice(insertIdx + 1, 0, blk)
  nextTick(() => {
    const idx = insertIdx + 1
    const el = editBlockRefs[idx]
    if (el) el.focus()
  })
  emit('flash', '已新建分块')
}

function splitBlock() {
  closeEtoolPops()
  restoreRange()
  const sel = window.getSelection()
  if (!sel || !sel.rangeCount) { emit('flash', '请先点选要分割的位置'); return }
  const node = sel.anchorNode
  const el = node && (node.nodeType === 1 ? node : node.parentElement)
  const txt = el && el.closest ? el.closest('.eblk-txt') : null
  if (!txt) { emit('flash', '请先点选要分割的分块'); return }
  const idx = editBlocks.value.findIndex(b => {
    const ref = editBlockRefs[editBlocks.value.indexOf(b)]
    return ref === txt || ref?.contains(txt)
  })
  if (idx < 0) return
  pushEditHistory()
  const range = sel.getRangeAt(0).cloneRange()
  range.setEnd(txt, txt.childNodes.length)
  const tail = range.extractContents()
  const tailHtml = tail.textContent?.trim() ? Array.from(tail.childNodes).map(n => n.outerHTML || n.textContent).join('') : '<p><br></p>'
  const origChapterId = editBlocks.value[idx]?.chapterId
  editBlocks.value.splice(idx + 1, 0, { id: nextBlockId++, html: tailHtml, chapterId: origChapterId, picked: false, splitOpen: false })
  emit('flash', '已分割分块')
}

const imageInputRef = ref(null)
let pendingImageInsertIdx = -1

function getCursorBlockIndex() {
  const sel = window.getSelection()
  const node = sel?.rangeCount ? sel.anchorNode : null
  const txt = hostOf(node)?.closest?.('.eblk-txt')
  const inEditor = txt && txt.closest?.('#editBody')
  if (inEditor) {
    for (let i = 0; i < editBlocks.value.length; i++) {
      const ref = editBlockRefs[i]
      if (ref && (ref === txt || ref.contains?.(txt) || txt.contains?.(ref))) return i
    }
  }
  const active = document.activeElement
  const activeTxt = active?.closest?.('.eblk-txt')
  if (activeTxt?.closest?.('#editBody')) {
    for (let i = 0; i < editBlocks.value.length; i++) {
      const ref = editBlockRefs[i]
      if (ref && (ref === active || ref === activeTxt || ref.contains?.(active))) return i
    }
  }
  return -1
}

// 插入图片：打开本地文件选择器
function pickImage() {
  closeEtoolPops()
  pendingImageInsertIdx = getCursorBlockIndex()
  markDirty()
  imageInputRef.value?.click()
}

// 选图后：压缩为内嵌 base64；有光标则插在该块下方，否则接到最后
function handleImagePicked(e) {
  const input = e.target
  const file = input?.files && input.files[0]
  if (input) input.value = ''   // 允许重复选择同一文件
  if (!file) return
  if (!file.type.startsWith('image/')) {
    emit('flash', '请选择图片文件')
    return
  }
  const afterIdx = pendingImageInsertIdx
  pendingImageInsertIdx = -1
  const insertAt = afterIdx >= 0 ? afterIdx + 1 : editBlocks.value.length
  const origin = editBlocks.value[afterIdx >= 0 ? afterIdx : editBlocks.value.length - 1]
  pushEditHistory()
  const reader = new FileReader()
  reader.onload = () => {
    compressImage(reader.result, file.type, (finalUrl) => {
      const blk = {
        id: nextBlockId++,
        html: `<figure class="blk-img"><img src="${finalUrl}" alt="插入的图片" /></figure>`,
        chapterId: origin?.chapterId,
        picked: false,
        splitOpen: false
      }
      editBlocks.value.splice(insertAt, 0, blk)
      nextTick(() => {
        editBlockRefs[insertAt]?.closest?.('.eblk')?.scrollIntoView({ block: 'nearest' })
      })
      emit('flash', '已插入图片')
    })
  }
  reader.readAsDataURL(file)
}

// 把大图等比例压缩到 maxWidth 内，避免内嵌 base64 撑爆保存内容
function compressImage(dataUrl, mime, done) {
  const img = new Image()
  img.onload = () => {
    try {
      const MAX = 1000
      if (img.width <= MAX && img.height <= MAX) { done(dataUrl); return }
      const scale = MAX / Math.max(img.width, img.height)
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(img.width * scale)
      canvas.height = Math.round(img.height * scale)
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
      const outMime = mime === 'image/png' || mime === 'image/gif' ? 'image/png' : 'image/jpeg'
      done(canvas.toDataURL(outMime, 0.88))
    } catch (err) {
      console.warn('图片压缩失败，使用原图', err)
      done(dataUrl)
    }
  }
  img.onerror = () => done(dataUrl)
  img.src = dataUrl
}

// Edit click & selection
function handleEditClick(e) {
  if (isTextDragOrSelect(e)) return
  if (e.target.closest('.eblk-check')) return
  if (isBatch.value && !e.target.closest('.eblk-txt')) {
    const blk = e.target.closest('.eblk')
    if (blk) {
      const idx = editBlocks.value.findIndex(b => {
        const ref = editBlockRefs[editBlocks.value.indexOf(b)]
        return ref?.closest?.('.eblk') === blk
      })
      if (idx >= 0) {
        editBlocks.value[idx].picked = !editBlocks.value[idx].picked
      }
    }
  }
}

function handleEditMouseDown(e) {
  if (e.target.closest('.eblk-split') || e.target.closest('.eblk-split-pop')) return
  closeSplitPops()
  if (brushOn.value) brushStroke = true
}

// document-level mousedown 委托：编辑视图内点击公式弹出编辑器
function handleDocFormulaMousedown(e) {
  if (!isEditing.value) return
  const mathEl = e.target.closest && e.target.closest('.math, [data-math]')
  const katexEl = !mathEl && e.target.closest && e.target.closest('.katex')
  const eblk = e.target.closest('.eblk-txt')
  if (eblk) {
    console.log('[formula] DOM check - math elements in eblk:', eblk.querySelectorAll('.math').length, 'katex:', eblk.querySelectorAll('.katex').length)
  }
  console.log('[formula] mousedown mathEl:', !!mathEl, 'katexEl:', !!katexEl, 'eblk:', !!eblk, 'tag:', e.target.tagName, 'class:', e.target.className)
  if (!mathEl && !katexEl) return
  if (!eblk) return
  e.preventDefault()
  e.stopPropagation()
  const targetEl = mathEl || katexEl
  mathEdit.el = targetEl
  // 对于 .math 元素，data-math 就在元素自身；对于 vditor 的 .katex 元素，data-math 在父级 .language-math 上
  mathEdit.value = targetEl.getAttribute('data-math') || (targetEl.closest('[data-math]') ? targetEl.closest('[data-math]').getAttribute('data-math') : '') || ''
  mathEdit.visible = true
  readMathPreview()
  hideSelbar()
  const r = targetEl.getBoundingClientRect()
  const w = 460
  const left = Math.max(12, Math.min(r.left, window.innerWidth - w - 12))
  const top = r.bottom + 10 < window.innerHeight - 80 ? r.bottom + 10 : Math.max(12, r.top - 150)
  mathEditStyle.value = { left: left + 'px', top: top + 'px' }
  nextTick(() => {
    const ta = mathInputRef.value
    if (ta) { ta.focus(); ta.select() }
  })
}

function onEblkMouseDown(e) {
  const mathEl = e.target.closest && e.target.closest('.math')
  console.log('[formula] onEblkMouseDown', { mathEl: !!mathEl, targetTag: e.target.tagName })
  if (!mathEl) return
  e.preventDefault()
  e.stopPropagation()
  mathEdit.el = mathEl
  mathEdit.value = mathEl.getAttribute('data-math') || ''
  mathEdit.visible = true
  readMathPreview()
  hideSelbar()
  const r = mathEl.getBoundingClientRect()
  const w = 460
  const left = Math.max(12, Math.min(r.left, window.innerWidth - w - 12))
  const top = r.bottom + 10 < window.innerHeight - 80 ? r.bottom + 10 : Math.max(12, r.top - 150)
  mathEditStyle.value = { left: left + 'px', top: top + 'px' }
  nextTick(() => {
    const ta = mathInputRef.value
    if (ta) { ta.focus(); ta.select() }
  })
}

function handleEditMouseUp() {
  if (brushOn.value) {
    hideSelbar()
    return
  }
  setTimeout(placeSelbar, 0)
}

function handleEditKeydown(e) {
  if (handleEditUndoHotkey(e)) return
  if (e.key === 'Escape') {
    if (selbarVisible.value) hideSelbar()
  }
}

// Selection toolbar
function restoreRange() {
  console.log('[restoreRange] savedRange:', savedRange ? 'exists' : 'null')
  if (!savedRange) {
    // Try to use current selection
    const sel = window.getSelection()
    console.log('[restoreRange] no savedRange, trying current selection. rangeCount:', sel?.rangeCount)
    if (sel && sel.rangeCount) savedRange = sel.getRangeAt(0).cloneRange()
    if (!savedRange) { console.log('[restoreRange] FAIL: no savedRange and no current selection'); return }
  }
  const sel = window.getSelection()
  sel.removeAllRanges()
  sel.addRange(savedRange)
  console.log('[restoreRange] restored range, now rangeCount:', sel.rangeCount, 'isCollapsed:', sel.isCollapsed)
}

function selectionInEditor() {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || !sel.rangeCount) { console.log('[selectionInEditor] no valid selection:', { exists: !!sel, isCollapsed: sel?.isCollapsed, rangeCount: sel?.rangeCount }); return null }
  const node = sel.anchorNode
  const el = node && (node.nodeType === 1 ? node : node.parentElement)
  const inEditor = el && el.closest && el.closest('#editBody')
  console.log('[selectionInEditor] inEditor:', !!inEditor, 'anchorNode:', node?.nodeName, 'el.tagName:', el?.tagName)
  if (!el || !el.closest || !el.closest('#editBody')) return null
  return sel
}

function placeSelbar() {
  if (!isEditing.value) { hideSelbar(); return }
  if (brushOn.value) { hideSelbar(); return }
  if (selInVditor()) { hideSelbar(); return }
  const sel = selectionInEditor()
  if (!sel) { hideSelbar(); return }
  savedRange = sel.getRangeAt(0).cloneRange()
  toolbarRange = savedRange.cloneRange()
  saveToolbarSelMeta()
  selbarPinned = false
  if (!positionSelbarAtRange(savedRange)) hideSelbar()
}

function hideSelbar() {
  selbarVisible.value = false
  selbarPinned = false
  toolbarRange = null
  toolbarSelMeta = null
  selOpen.style = false
  selOpen.color = false
}

// ---- 公式编辑（双击 .math 元素，即 <latex-formula>）：改 LaTeX 源码，写回 data-math 并重渲染 ----
const mathEdit = reactive({ visible: false, el: null, value: '' })
const mathEditStyle = ref({})
const mathEditError = ref('')
const mathEditPreview = ref('')
const mathInputRef = ref(null)

function onMathDblclick(e) {
  const sp = e.target.closest && e.target.closest('.math')
  // 只响应编辑视图内（.eblk-txt）的公式，阅读视图双击不弹
  if (!sp || !e.target.closest('.eblk-txt')) return
  e.preventDefault()
  e.stopPropagation()
  mathEdit.el = sp
  mathEdit.value = sp.getAttribute('data-math') || ''
  mathEdit.visible = true
  readMathPreview()
  hideSelbar()
  // 浮层贴在公式下方，空间不足移到上方；与 selbar 相同的 fixed 定位方式
  const r = sp.getBoundingClientRect()
  const w = 460
  const left = Math.max(12, Math.min(r.left, window.innerWidth - w - 12))
  const top = r.bottom + 10 < window.innerHeight - 80 ? r.bottom + 10 : Math.max(12, r.top - 150)
  mathEditStyle.value = { left: left + 'px', top: top + 'px' }
  nextTick(() => {
    const ta = mathInputRef.value
    if (ta) { ta.focus(); ta.select() }
  })
}

// 输入时实时预览；KaTeX 报错文本从 katex-error title 里取（throwOnError:false 时）
function readMathPreview() {
  const tex = (mathEdit.value || '').trim()
  if (!tex) { mathEditPreview.value = ''; mathEditError.value = ''; return }
  const html = katex.renderToString(tex, { displayMode: tex.includes('\n'), throwOnError: false, strict: false })
  const m = html.match(/class="katex-error"[^>]*title="([^"]*)"/)
  if (m) {
    mathEditError.value = decodeHtmlEnt(m[1])
    mathEditPreview.value = ''
  } else {
    mathEditError.value = ''
    mathEditPreview.value = html
  }
}

function decodeHtmlEnt(s) {
  const t = document.createElement('textarea')
  t.innerHTML = s
  return t.value
}

function onMathEditorKeydown(e) {
  if (e.key === 'Escape') { closeMathEditor(); return }
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { applyMathEdit() }
}

function applyMathEdit() {
  const sp = mathEdit.el
  if (sp && mathEdit.visible) {
    pushEditHistory()
    const tex = (mathEdit.value || '').trim()
    // 对于 vditor 的 KaTeX 元素，data-math 在父级 .language-math 上
    const mathContainer = sp.classList.contains('katex') ? (sp.closest('[data-math]') || sp) : sp
    if (tex) {
      // 源码 + 渲染结果一起更新；保存链路只读 data-math，改这里即改入库内容
      mathContainer.setAttribute('data-math', tex)
      mathContainer.innerHTML = katex.renderToString(tex, { displayMode: tex.includes('\n'), throwOnError: false, strict: false })
    } else {
      // 清空公式：还原为纯文本分隔符（与空内容保存语义一致，单美元协议）
      mathContainer.replaceWith(document.createTextNode('$'))
    }
    // 程序改 innerHTML 不触发 input，手动同步回 editBlocks 并标记脏
    const idx = editBlockRefs.findIndex(ref => ref && ref.contains(sp))
    if (idx >= 0) {
      const blk = editBlocks.value[idx]
      if (blk.isTable) {
        // vditor 表格块：触发 input 事件让 vditor 同步到 blk.txt
        const v = vditorInsts[blk.id]
        if (v && v.vditor) {
          const el = v.vditor.element
          if (el) el.dispatchEvent(new Event('input', { bubbles: true }))
        }
      } else {
        blk.html = editBlockRefs[idx].innerHTML
      }
    }
    markDirty()
  }
  closeMathEditor()
}

function closeMathEditor() {
  mathEdit.visible = false
  mathEdit.el = null
  mathEdit.value = ''
  mathEditPreview.value = ''
  mathEditError.value = ''
}

// 在 mathEdit 工具栏中插入 LaTeX 模板到光标位置，并选中占位区域
function insertMathTpl(tpl) {
  const ta = mathInputRef.value
  if (!ta) return
  const start = ta.selectionStart
  const end = ta.selectionEnd
  const sel = mathEdit.value.substring(start, end)
  // 如果选中了文本，用选中文本替换模板中的 {} 占位
  let insert
  if (sel && tpl.includes('{}')) {
    insert = tpl.replace('{}', sel)
  } else {
    insert = sel ? tpl.replace(/\{\}/g, sel) : tpl
  }
  const before = mathEdit.value.substring(0, start)
  const after = mathEdit.value.substring(end)
  mathEdit.value = before + insert + after
  nextTick(() => {
    ta.focus()
    // 定位光标到插入模板的末尾
    const newPos = start + insert.length
    ta.setSelectionRange(newPos, newPos)
    readMathPreview()
  })
}

function updateSelbarActive() {
  const map = { bold: 'bold', italic: 'italic', underline: 'underline', strike: 'strikeThrough' }
  Object.keys(map).forEach(act => {
    if (act === 'underline') selStates.underline = inlineDecoActive('underline')
    else if (act === 'strike') selStates.strike = inlineDecoActive('strikeThrough')
    else if (act === 'bold') selStates.bold = isUserBoldActive()
    else {
      try { selStates[act] = document.queryCommandState(map[act]) } catch { selStates[act] = false }
    }
  })
  // Check if in cloze
  const sel = window.getSelection()
  if (sel && sel.anchorNode) {
    const el = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement
    selInCloze.value = !!(el && el.closest && el.closest('customclickablespan'))
  }
}

function toggleSelPopup(name) {
  if (selOpen[name]) {
    selOpen[name] = false
  } else {
    selOpen.style = false
    selOpen.color = false
    selOpen[name] = true
  }
}

function applySelStyle(style) {
  pushEditHistory()
  restoreRange()
  if (style === 'ol') document.execCommand('insertOrderedList')
  else if (style === 'ul') document.execCommand('insertUnorderedList')
  else document.execCommand('formatBlock', false, style)
  selOpen.style = false
}

function applySelCmd(cmd) {
  pinSelbarAction()
  if (cmd === 'underline' || cmd === 'strikeThrough') {
    toggleInlineDecoration(cmd)
    return
  }
  pushEditHistory()
  if (!restoreToolbarSelection()) restoreRange()
  if (cmd === 'bold') toggleUserBold()
  else document.execCommand(cmd)
  finishSelbarAction()
}

function applySelColor(color) {
  pinSelbarAction()
  pushEditHistory()
  if (!restoreToolbarSelection()) restoreRange()
  document.execCommand('styleWithCSS', false, true)
  document.execCommand('foreColor', false, color)
  selOpen.color = false
  finishSelbarAction()
}

function applySelCloze() {
  pinSelbarAction()
  if (!restoreToolbarSelection()) restoreRange()
  const sel = window.getSelection()
  if (!sel?.rangeCount || sel.isCollapsed) {
    emit('flash', '请先选中要挖空的文字')
    return
  }
  saveToolbarSelMeta()
  pushEditHistory()
  const range = sel.getRangeAt(0).cloneRange()
  const result = applyClozeRange(range, editBodyRef.value)
  emit('flash', result === 'removed' ? '已取消挖空' : '已挖空')
  finishFormatAction(true)
}

// ===== AI Operations =====
const AI_JOB_MS = 2700
const AI_STEPS = {
  cloze: ['正在进行文章理解…', '正在进行关键词识别…', '正在进行挖空生成…'],
  chunk: ['正在进行段落分析…', '正在进行知识点拆分…', '正在进行分块整理…'],
  rule: ['正在按规则扫描内容…', '正在匹配符号与关键词…', '正在生成挖空结果…'],
  tpl: ['正在按模版计算间隔…', '正在应用隐藏规则…', '正在生成挖空结果…']
}

// CzModal integration
const czModalVisible = ref(false)
const czKind = ref('ai')
const czState = reactive({
  kind: 'ai', density: 40, step: 'settings', scope: 'full', chapFrom: 0, chapTo: null,
  rule: { num: false, year: false, en: false, custom: false, paren: false, bracket: false, corner: false, quote: false, symCustom: false },
  customWords: '', customSymbol: '',
  unit: 'char', interval: 'fixed', gap: 3, hide: 3
})

// AiMask integration
const aiMaskVisible = ref(false)
const aiMaskText = ref('')
let aiJobTimers = []
let aiJobRunning = false
const czPickVisible = ref(false)
const czPickStyle = ref({})
const czPickRef = ref(null)
const aiClozeBtnRef = ref(null)
let pendingCzRun = null
const aiConfirm = reactive({ visible: false, kind: '' })
const aiConfirmText = computed(() => {
  if (aiConfirm.kind === 'chunk') return 'AI快速分块后，将覆盖已有分块结果，是否确认？'
  if (aiConfirm.kind === 'cloze') return 'AI快速挖空后，将覆盖已有挖空结果，是否确认？'
  return ''
})

function requestAiConfirm(kind) {
  if (aiBusy.value && aiJobRunning) return
  czPickVisible.value = false
  closeEtoolPops()
  aiConfirm.kind = kind
  aiConfirm.visible = true
}

function cancelAiConfirm() {
  aiConfirm.visible = false
  aiConfirm.kind = ''
  pendingCzRun = null
}

function confirmAiAction() {
  const kind = aiConfirm.kind
  const pending = pendingCzRun
  cancelAiConfirm()
  if (kind === 'chunk') openChunkScope()
  else if (kind === 'cloze' && pending) startCzRun(pending)
}

function openCzModal(kind) {
  czPickVisible.value = false
  czKind.value = kind
  czState.kind = kind
  czState.step = 'settings'
  czModalVisible.value = true
}

function openChunkScope() {
  // 自我修复：早前任务异常中断导致的残留锁，先重置再继续
  if (aiJobRunning) {
    aiJobRunning = false
    aiBusy.value = false
    aiLock.value = false
    hideAiMask()
  }
  czPickVisible.value = false
  // 不再弹「选择生效范围」：点击后直接对当前这一章做 AI 分块
  czKind.value = 'chunk'
  czState.kind = 'chunk'
  czState.scope = 'chapter'
  const { from, to } = currentChapterBlockRange()
  czState.chapFrom = from
  czState.chapTo = to
  withAiJob('chunk', { run: runAiChunk, done: () => {
    flash('已AI快速分块')
  }})
}

// 当前章在 editBlocks 中的索引范围（以第一个带 chapterId 的块为准；
// 新建文档无 chapterId 时视为单章，范围为全部分块）
function currentChapterBlockRange() {
  const blocks = editBlocks.value
  if (!blocks.length) return { from: 0, to: 0 }
  const first = blocks.find(b => b.chapterId)
  const chapterId = first ? first.chapterId : null
  if (chapterId == null) return { from: 0, to: blocks.length - 1 }
  const from = blocks.findIndex(b => b.chapterId === chapterId)
  let to = blocks.length - 1
  for (let i = from + 1; i < blocks.length; i++) {
    if (blocks[i].chapterId !== chapterId) { to = i - 1; break }
  }
  return { from, to }
}

function handleCzRun(state) {
  pendingCzRun = { ...state }
  aiConfirm.kind = 'cloze'
  aiConfirm.visible = true
}

function startCzRun(state) {
  czModalVisible.value = false
  Object.assign(czState, state)
  ensureEditThen(() => {
    if (czState.kind === 'chunk') {
      withAiJob('chunk', { run: runAiChunk, done: () => {
        flash('已AI快速分块')
      }})
    } else if (czState.kind === 'ai') {
      // 不再选择生效范围：只对当前这一章执行 AI 挖空
      czState.scope = 'chapter'
      const range = currentChapterBlockRange()
      czState.chapFrom = range.from
      czState.chapTo = range.to
      withAiJob('cloze', { run: runAiCloze, done: (n) => {
        flash(n ? `已在当前章挖空 ${n} 处` : '没有更多可挖空的词了')
      }})
    } else if (czState.kind === 'rule') {
      // 不再选择生效范围：只对当前这一章执行规则挖空
      czState.scope = 'chapter'
      const range = currentChapterBlockRange()
      czState.chapFrom = range.from
      czState.chapTo = range.to
      withAiJob('rule', { run: runRuleCloze, done: (n) => {
        flash(n ? `已在当前章按规则挖空 ${n} 处` : '没有匹配到可挖空内容')
      }})
    } else {
      // 不再选择生效范围：只对当前这一章执行模版挖空
      czState.scope = 'chapter'
      const range = currentChapterBlockRange()
      czState.chapFrom = range.from
      czState.chapTo = range.to
      withAiJob('tpl', { run: runTplCloze, done: (n) => {
        flash(n ? `已在当前章按模版挖空 ${n} 处` : '当前间隔下无可挖空内容')
      }})
    }
  })
}

function ensureEditThen(fn) {
  if (!isEditing.value) {
    enterEdit()
    requestAnimationFrame(fn)
    return
  }
  fn()
}

function getClozeRoots() {
  const box = editBodyRef.value
  if (!box) return []
  if (czState.scope !== 'chapter') return [box]
  const blks = editBlocks.value
  const from = czState.chapFrom == null ? 0 : czState.chapFrom
  const to = czState.chapTo == null ? from : czState.chapTo
  const min = Math.min(from, to)
  const max = Math.max(from, to)
  return blks.slice(min, max + 1).map((b, i) => editBlockRefs[min + i] || box)
}

// 在单个文本节点上按偏移量抠出指定文本包成挖空span，返回剩余文本节点（供继续遍历）
function insertClozeSpan(node, idx, text) {
  const orig = node.nodeValue
  if (!orig || idx < 0 || idx + text.length > orig.length) return null
  const before = orig.slice(0, idx)
  const match = orig.slice(idx, idx + text.length)
  const after = orig.slice(idx + text.length)
  const parent = node.parentNode
  if (!parent) return null
  // 如果已经在挖空 span 内则不重复挖
  if (parent.closest && parent.closest('customclickablespan')) return null
  const span = document.createElement('customclickablespan')
  span.className = 'ai-new'
  span.setAttribute('data-pre-bold', '0')
  span.textContent = match
  const frag = document.createDocumentFragment()
  if (before) frag.appendChild(document.createTextNode(before))
  frag.appendChild(span)
  let afterNode = null
  if (after) {
    afterNode = document.createTextNode(after)
    frag.appendChild(afterNode)
  }
  parent.replaceChild(frag, node)
  isolateClozeDecorations(span)
  applyDefaultClozeBold(span)
  revealClozeElement(span)
  return afterNode
}

// AI Cloze — 调用后端 batchWordHollow 接口（入参为每块纯文本，返回关键词下标区间）
function wrapClozeRange(el, start, end) {
  let sNode = null, sOff = 0, eNode = null, eOff = 0
  let acc = 0
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
  let node
  while ((node = walker.nextNode())) {
    const len = (node.data || '').length
    if (sNode === null && acc + len > start) { sNode = node; sOff = start - acc }
    if (acc + len >= end) { eNode = node; eOff = end - acc; break }
    acc += len
  }
  if (!sNode || !eNode) return false
  // 已经在挖空 span 内的不重复挖
  const p = sNode.parentElement
  if (p && p.closest && p.closest('customclickablespan')) return false
  const range = document.createRange()
  range.setStart(sNode, sOff)
  range.setEnd(eNode, eOff)
  const preBold = isRangeFullyBold(range)
  const textColor = rangeTextColor(range)
  const span = document.createElement('customclickablespan')
  span.className = 'ai-new'
  span.setAttribute('data-pre-bold', preBold ? '1' : '0')
  if (textColor) span.style.color = textColor
  try {
    range.surroundContents(span)
  } catch (err) {
    span.appendChild(range.extractContents())
    range.insertNode(span)
  }
  span.querySelectorAll(CLOZE_TAG).forEach(unwrapCloze)
  isolateClozeDecorations(span)
  if (textColor && !span.style.color) span.style.color = textColor
  applyDefaultClozeBold(span)
  revealClozeElement(span)
  return true
}

async function runAiCloze() {
  const blocks = getChunkBlocks()
  const scope = blocks.map(blk => {
    const el = editBlockRefs[editBlocks.value.indexOf(blk)]
    return { blk, el, plain: el ? (el.textContent || '') : '' }
  }).filter(it => it.el && it.plain.replace(/\s/g, ''))
  if (!scope.length) return 0
  pushEditHistory()

  const bookId = scope[0].blk.chapterId || props.currentDoc || ''
  console.log('[AI挖空] 请求 batchWordHollow, blocks:', scope.map(it => it.plain))
  // 后端 AI 关键词提取最长约 45s，超时放宽到 60s
  const res = await bookApi.batchWordHollow({
    bookId,
    keyWords: 0,
    batchWordHollow: scope.map(it => ({ id: String(it.blk.id), article: it.plain }))
  }, { timeout: 60000 })
  console.log('[AI挖空] 响应:', res)
  if (!res || res.code !== 0) throw new Error((res && res.msg) || '挖空失败，请稍后重试')

  const byId = {}
  ;(res.data || []).forEach(vo => {
    if (vo && vo.id != null) byId[String(vo.id)] = vo.wordHollow
  })

  let n = 0
  scope.forEach(it => {
    const hollow = byId[String(it.blk.id)]
    const ranges = []
    ;((hollow && hollow.wordIndexBeans) || []).forEach(w => {
      ;(w.strIndexBeans || []).forEach(si => {
        const s = Number(si.startIndex)
        const e = Number(si.endIndex)
        if (Number.isFinite(s) && Number.isFinite(e) && e > s) {
          ranges.push([Math.max(0, s), Math.min(it.plain.length, e)])
        }
      })
    })
    if (!ranges.length) return
    it.el.querySelectorAll('customclickablespan.ai-new').forEach(el => el.classList.remove('ai-new'))
    // 排序并合并重叠区间，按下标把关键词包成挖空 span
    const merged = []
    ranges.sort((a, b) => a[0] - b[0]).forEach(r => {
      const last = merged[merged.length - 1]
      if (last && r[0] <= last[1]) last[1] = Math.max(last[1], r[1])
      else merged.push([...r])
    })
    merged.forEach(([s, e]) => { if (wrapClozeRange(it.el, s, e)) n++ })
    // 同步块内容，保证保存与脏检查正确
    it.blk.html = it.el.innerHTML
  })
  return n
}

// Rule Cloze
function wrapByFinders(root, finders) {
  let n = 0
  function walk(node) {
    if (node.nodeType === 1) {
      if (node.tagName === 'CUSTOMCLICKABLESPAN') return
      Array.from(node.childNodes).forEach(walk)
      return
    }
    if (node.nodeType !== 3) return
    const text = node.nodeValue
    if (!text || !/[^\s　]/.test(text)) return
    let best = null
    for (const fn of finders) {
      const hit = fn(text)
      if (!hit) continue
      if (!best || hit.idx < best.idx || (hit.idx === best.idx && hit.text.length > best.text.length)) best = hit
    }
    if (!best) return
    const rest = insertClozeSpan(node, best.idx, best.text)
    n++
    if (rest) walk(rest)
  }
  walk(root)
  return n
}

function finderString(term) {
  return text => {
    const at = text.indexOf(term)
    return at < 0 ? null : { idx: at, text: term }
  }
}

function finderRegex(re, group) {
  return text => {
    const m = text.match(re)
    if (!m) return null
    if (group && m[1] != null) {
      const innerAt = text.indexOf(m[1], m.index)
      return { idx: innerAt < 0 ? m.index : innerAt, text: m[1] }
    }
    return { idx: m.index, text: m[0] }
  }
}

function runRuleCloze() {
  pushEditHistory()
  const roots = getClozeRoots()
  const finders = []
  const r = czState.rule
  if (r.num) finders.push(finderRegex(/\d+(?:\.\d+)?/))
  if (r.year) finders.push(finderRegex(/(?:19|20)\d{2}年?/))
  if (r.en) finders.push(finderRegex(/[A-Za-z][A-Za-z0-9+\-]{1,}/))
  if (r.custom) {
    (czState.customWords || '').split(/[,，、\s]+/).forEach(w => { if (w) finders.push(finderString(w)) })
  }
  if (r.paren) finders.push(finderRegex(/[（(]([^）)]+)[）)]/, true))
  if (r.bracket) finders.push(finderRegex(/\[([^\]]+)\]/, true))
  if (r.corner) finders.push(finderRegex(/【([^】]+)】/, true))
  if (r.quote) finders.push(finderRegex(/[“"]([^”"]+)[”"]/, true))
  if (r.symCustom && czState.customSymbol) finders.push(finderString(czState.customSymbol))
  if (!finders.length || !roots.length) return 0
  let n = 0
  roots.forEach(box => {
    box.querySelectorAll('customclickablespan.ai-new').forEach(el => el.classList.remove('ai-new'))
    n += wrapByFinders(box, finders)
  })
  revealEditClozes()
  return n
}

// Template Cloze
function collectTplUnits(root, unit) {
  const units = []
  function walk(node) {
    if (node.nodeType === 1) {
      if (node.tagName === 'CUSTOMCLICKABLESPAN') return
      Array.from(node.childNodes).forEach(walk)
      return
    }
    if (node.nodeType !== 3) return
    const t = node.nodeValue
    let i = 0
    while (i < t.length) {
      if (/\s/.test(t.charAt(i))) { i++; continue }
      if (unit === 'word') {
        const m = t.slice(i).match(/^[A-Za-z0-9+\-]+|^[一-\u9fff]{1,2}|^./)
        if (!m) break
        units.push({ node, idx: i, text: m[0] })
        i += m[0].length
      } else {
        units.push({ node, idx: i, text: t.charAt(i) })
        i++
      }
    }
  }
  walk(root)
  return units
}

function applyTplMarks(units, gap, hideN, random) {
  const marks = []
  let skip = 0, hid = 0, mode = 'skip', g = gap, h = hideN
  for (let i = 0; i < units.length; i++) {
    if (mode === 'skip') {
      skip++
      if (skip >= g) { mode = 'hide'; hid = 0; if (random) h = Math.max(1, hideN + (Math.random() < 0.5 ? -1 : 1)) }
    } else {
      marks.push(i)
      hid++
      if (hid >= h) { mode = 'skip'; skip = 0; if (random) g = Math.max(1, gap + (Math.random() < 0.5 ? -1 : 1)) }
    }
  }
  let n = 0
  for (let i = marks.length - 1; i >= 0; i--) {
    const u = units[marks[i]]
    if (!u.node || !u.node.parentNode) continue
    insertClozeSpan(u.node, u.idx, u.text)
    n++
  }
  return n
}

function runTplCloze() {
  pushEditHistory()
  const roots = getClozeRoots()
  const gap = Math.max(1, parseInt(czState.gap, 10) || 3)
  const hideN = Math.max(1, parseInt(czState.hide, 10) || 3)
  const random = czState.interval === 'random'
  let total = 0
  roots.forEach(box => {
    box.querySelectorAll('customclickablespan.ai-new').forEach(el => el.classList.remove('ai-new'))
    if (czState.unit === 'para') {
      const paras = Array.from(box.querySelectorAll('p, h1, h2, h3'))
      let skip = 0, hid = 0, mode = 'skip', g = gap, h = hideN
      paras.forEach(p => {
        if (!(p.textContent || '').trim()) return
        if (mode === 'skip') { skip++; if (skip >= g) { mode = 'hide'; hid = 0 } }
        else {
          const preBold = isContentFullyBold(p)
          const span = document.createElement('customclickablespan')
          span.className = 'ai-new'
          span.setAttribute('data-pre-bold', preBold ? '1' : '0')
          span.innerHTML = p.innerHTML
          p.innerHTML = ''
          p.appendChild(span)
          isolateClozeDecorations(span)
          applyDefaultClozeBold(span)
          revealClozeElement(span)
          total++
          hid++
          if (hid >= h) { mode = 'skip'; skip = 0; if (random) g = Math.max(1, gap + (Math.random() < 0.5 ? -1 : 1)) }
        }
      })
      return
    }
    total += applyTplMarks(collectTplUnits(box, czState.unit === 'word' ? 'word' : 'char'), gap, hideN, random)
  })
  revealEditClozes()
  return total
}

// AI Chunk — 调用后端 generateBlock 接口（入参为纯文本 txt，返回纯文本分块，需匹配回富文本）
const AI_CHUNK_MAX_CHARS = 0

// 把后端返回的纯文本分块定位到原富文本中的切割偏移
function matchChunksToCuts(plain, chunks) {
  // 后端返回的每个分块都是原文（plain）的连续子串（内部通过 indexOf 在原文本上定位后截取），
  // 因此按顺序累计即可得到各分块在原文本中的切割点
  const cuts = []
  let pos = 0
  for (const ch of chunks) {
    const idx = plain.indexOf(ch, pos)
    pos = (idx >= 0 ? idx : pos) + ch.length
    cuts.push(pos)
  }
  // 最后一段的结束位置就是文末，首段起点就是文首，都不是切割点
  cuts.pop()
  return [...new Set(cuts.map(c => Math.max(0, Math.min(plain.length, c))).filter(c => c > 0 && c < plain.length))]
    .sort((a, b) => a - b)
}

// 按字符偏移量切割富文本 HTML（保留原有格式），返回各段 HTML 字符串
function splitRichHtmlByOffsets(html, cuts) {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const root = doc.body
  if (!root || !root.firstChild) return [html]

  // 1. 收集所有文本节点及其在原文本中的起止偏移
  const textNodes = []
  let total = 0
  const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  while (walker.nextNode()) {
    const n = walker.currentNode
    textNodes.push({ node: n, s: total, e: total + n.data.length })
    total += n.data.length
  }

  // 2. 在每个切割点处拆分文本节点，得到边界标记节点
  const markers = []
  const remainders = new Map() // 原文本节点 → { node: 当前剩余文本节点, start: 其起始偏移 }
  cuts.forEach(cut => {
    const tn = textNodes.find(t => cut >= t.s && cut <= t.e)
    if (!tn) return
    const cur = remainders.get(tn.node) || { node: tn.node, start: tn.s }
    if (cut === cur.start) { markers.push(cur.node); return }
    const rem = cur.node.splitText(cut - cur.start)
    remainders.set(tn.node, { node: rem, start: cut })
    markers.push(rem)
  })
  markers.sort((a, b) => a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1)
  if (!markers.length) return [html]

  // 3. 用 Range 逐段提取并序列化（markers[i] 属于其后的片段）
  const pieces = []
  const extract = (range) => {
    const frag = range.extractContents()
    if (!frag.firstChild) return
    const w = doc.createElement('div')
    w.appendChild(frag)
    pieces.push(w.innerHTML)
  }
  const r0 = doc.createRange()
  r0.setStart(root, 0)
  r0.setEnd(markers[0], 0)
  extract(r0)
  for (let i = 1; i < markers.length; i++) {
    const r = doc.createRange()
    r.setStart(markers[i - 1], 0)
    r.setEnd(markers[i], 0)
    extract(r)
  }
  const rN = doc.createRange()
  rN.setStart(markers[markers.length - 1], 0)
  rN.setEnd(root, root.childNodes.length)
  extract(rN)

  const result = pieces.map(p => p.trim()).filter(Boolean)
  return result.length ? result : [html]
}

async function runAiChunk() {
  const box = editBodyRef.value
  if (!box) return 0
  box.querySelectorAll('.eblk.ai-new').forEach(el => el.classList.remove('ai-new'))
  const blocks = getChunkBlocks()
  // 收集当前生效范围分块的纯文本（入参 txt）
  const scope = blocks.map(blk => {
    const el = editBlockRefs[editBlocks.value.indexOf(blk)]
    return { blk, el, plain: el ? (el.textContent || '') : '' }
  }).filter(it => it.el && it.plain.replace(/\s/g, ''))
  if (!scope.length) return 0
  pushEditHistory()

  console.log('[AI分块] 请求 generateBlock, blocks:', scope.map(it => it.plain))
  const res = await bookApi.generateBlock(scope.map(it => it.plain), AI_CHUNK_MAX_CHARS)
  console.log('[AI分块] 响应:', res)
  if (!res || res.code !== 0) throw new Error((res && res.msg) || '分块失败，请稍后重试')
  const groups = res.data || []

  let added = 0
  scope.forEach((it, i) => {
    const chunks = (groups[i] || []).map(c => (c || '').trim()).filter(Boolean)
    if (chunks.length < 2) return
    // 用后端纯文本分块的切割点，匹配回当前块的富文本，保留原格式
    const cuts = matchChunksToCuts(it.plain, chunks)
    if (!cuts.length) return
    const pieces = splitRichHtmlByOffsets(it.el.innerHTML, cuts)
    if (pieces.length <= 1) return
    it.el.innerHTML = pieces[0]
    let after = it.blk
    pieces.slice(1).forEach(html => {
      const nb = { id: nextBlockId++, html, picked: false, splitOpen: false }
      const idx = editBlocks.value.indexOf(after)
      editBlocks.value.splice(idx + 1, 0, nb)
      after = nb
      added++
    })
  })
  return added
}

function getChunkBlocks() {
  if (czState.scope !== 'chapter') return editBlocks.value
  const from = czState.chapFrom == null ? 0 : czState.chapFrom
  const to = czState.chapTo == null ? from : czState.chapTo
  const min = Math.min(from, to)
  const max = Math.max(from, to)
  return editBlocks.value.slice(min, max + 1)
}

// AI Job orchestration
function clearAiJobTimers() {
  aiJobTimers.forEach(id => clearTimeout(id))
  aiJobTimers = []
}

function setAiMaskText(msg) {
  aiMaskText.value = msg
}

function lockEditForAi(on) {
  aiLock.value = !!on
  if (on) {
    hideSelbar()
    closeEtoolPops()
    closeSplitPops()
  }
}

function showAiMask(kind) {
  const steps = AI_STEPS[kind] || AI_STEPS.cloze
  clearAiJobTimers()
  aiMaskVisible.value = true
  setAiMaskText(steps[0])
  const stepMs = Math.floor(AI_JOB_MS / steps.length)
  steps.slice(1).forEach((msg, i) => {
    aiJobTimers.push(setTimeout(() => setAiMaskText(msg), stepMs * (i + 1)))
  })
}

function hideAiMask() {
  clearAiJobTimers()
  aiMaskVisible.value = false
}

function withAiJob(kind, opts) {
  if (aiJobRunning) return
  aiJobRunning = true
  lockEditForAi(true)
  showAiMask(kind === 'rule' || kind === 'tpl' ? kind : (kind === 'chunk' ? 'chunk' : 'cloze'))
  aiBusy.value = true
  ;(async () => {
    let n = 0
    let err = null
    try {
      // 真实任务立即执行（网络请求即刻发出），遮罩至少展示 AI_JOB_MS 保证进度动画完整
      const [res] = await Promise.all([
        opts.run ? opts.run() : Promise.resolve(0),
        new Promise(r => setTimeout(r, AI_JOB_MS))
      ])
      n = res
    } catch (e) {
      err = e
    } finally {
      lockEditForAi(false)
      hideAiMask()
      aiBusy.value = false
      aiJobRunning = false
    }
    if (err) {
      flash((err && err.message) || 'AI 处理失败，请重试')
    } else if (opts.done) {
      opts.done(n)
    } else if (kind === 'chunk') {
      flash('已AI快速分块')
    } else {
      flash(n ? `已自动挖空 ${n} 处关键词` : '没有更多可挖空的词了')
    }
    markDirty()
  })()
}

// ===== persistReadDoc (save cloze changes in reading mode) =====
function persistReadDoc() {
  if (!scrollEl.value) return
  scrollEl.value.querySelectorAll('.d-sec').forEach(secEl => {
    const idx = parseInt(secEl.dataset.index, 10)
    const sec = sections.value[idx]
    if (Number.isNaN(idx) || !sec || sec.type === 'chapterTitle') return
    const back = secEl.querySelector('.kb-back')
    if (!back) return
    const html = editClozeToRead(back.innerHTML)
    sec.content = html
    back.__content = html
  })
  const wrap = document.createElement('div')
  wrap.innerHTML = scrollEl.value.innerHTML
  wrap.querySelectorAll('.kb-front').forEach(el => el.remove())
  wrap.querySelectorAll('.d-sec').forEach(sec => {
    sec.classList.remove('flipped')
    sec.removeAttribute('style')
    sec.removeAttribute('data-qtitle')
    const back = sec.querySelector('.kb-back')
    if (back) {
      while (back.firstChild) sec.insertBefore(back.firstChild, back)
      back.remove()
    }
  })
  flattenNestedClozes(wrap)
  const html = wrap.innerHTML
  emit('save-doc', html)
}

// ===== editClozeToRead (convert .e-cloze to customclickablespan for backward compat) =====
function editClozeToRead(html) {
  const wrap = document.createElement('div')
  wrap.innerHTML = html
  // 旧格式 .e-cloze 转为 customclickablespan
  wrap.querySelectorAll('.e-cloze').forEach(c => {
    const header = document.createElement('customclickablespan')

    header.textContent = c.textContent || ''
    c.parentNode.replaceChild(header, c)
  })
  // 保存时去掉 shown 类，阅读模式默认从隐藏状态开始
  flattenNestedClozes(wrap)
  normalizeClozeDecorations(wrap)
  consolidateAllClozeGroups(wrap)
  wrap.querySelectorAll('customclickablespan.shown').forEach(el => el.classList.remove('shown'))
  return wrap.innerHTML
}

// ===== placeAiClozePick with positioning =====
function openAiClozePick(event) {
  if (aiJobRunning) return
  czPickVisible.value = !czPickVisible.value
  if (czPickVisible.value) positionAiClozePick(event?.currentTarget || aiClozeBtnRef.value)
}

function positionAiClozePick(btn) {
  if (!btn) return
  const rect = btn.getBoundingClientRect()
  czPickStyle.value = {
    position: 'fixed',
    left: Math.max(12, rect.right - 168) + 'px',
    top: (rect.bottom + 6) + 'px'
  }
}

// ===== Navigation =====
function goHome() {
  emit('go-home')
}

function openShare() {
  emit('open-share')
}

function openFeedback() {
  emit('open-feedback')
}

// Keyboard shortcuts
function handleEditUndoHotkey(e) {
  if (!isEditing.value || e.defaultPrevented) return false
  if (e.target?.closest?.('textarea, input, .math-editor')) return false
  const key = (e.key || '').toLowerCase()
  if (!(e.metaKey || e.ctrlKey)) return false
  if (key === 'z') {
    e.preventDefault()
    if (e.shiftKey) applyEditRedo()
    else applyEditUndo()
    return true
  }
  if (key === 'y') {
    e.preventDefault()
    applyEditRedo()
    return true
  }
  return false
}

function handleKeydown(e) {
  if (handleEditUndoHotkey(e)) return
  if (e.key === 'Escape' && aiConfirm.visible) {
    cancelAiConfirm()
    return
  }
  if (etoolPopOpen() && !['Shift', 'Control', 'Alt', 'Meta'].includes(e.key)) {
    closeEtoolPops()
  }
  if (e.key === 'Escape' && brushOn.value) {
    setBrushOn(false)
    emit('flash', '挖空刷已关闭')
  }
  if (e.key === 'Escape' && czPickVisible.value) {
    czPickVisible.value = false
  }
  if (!isEditing.value && e.code === 'Space' && !e.target.tagName.match(/INPUT|TEXTAREA/) && !e.target.isContentEditable) {
    e.preventDefault()
    toggleAllCloze()
  }
}

// Global mouseup for selbar and cloze bubble
function handleGlobalMouseUp(e) {
  if (isEditing.value) {
    if (e?.target?.closest?.('.selbar')) return
    if (brushOn.value) {
      const paint = brushStroke && !selInVditor()
      brushStroke = false
      if (paint) setTimeout(() => applyBrushCloze(), 0)
      else hideSelbar()
      return
    }
    setTimeout(() => {
      if (e?.target?.closest?.('.selbar')) return
      const sel = selectionInEditor()
      if (sel && !sel.isCollapsed) {
        selbarPinned = false
        placeSelbar()
      } else {
        hideSelbar()
      }
    }, 0)
  } else {
    setTimeout(placeClozeBubble, 0)
  }
}

function handleGlobalSelectionChange() {
  if (!isEditing.value) return
  const sel = window.getSelection()
  if (sel && sel.rangeCount && !sel.isCollapsed) {
    const node = sel.anchorNode
    const el = node && (node.nodeType === 1 ? node : node.parentElement)
    const inEditor = el && el.closest && el.closest('#editBody')
    if (inEditor) {
      savedRange = sel.getRangeAt(0).cloneRange()
      toolbarRange = savedRange.cloneRange()
      saveToolbarSelMeta()
    }
  }
  if (!selectionInEditor()) {
    if (selbarInteracting) {
      updateSelbarActive()
      syncEtool()
      return
    }
    setTimeout(() => {
      if (selbarInteracting) return
      if (!selectionInEditor()) hideSelbar()
    }, 0)
  } else {
    updateSelbarActive()
    syncEtool()
  }
}

function handleDocMouseDown(e) {
  if (e.button === 0) {
    readPointer.x = e.clientX
    readPointer.y = e.clientY
  }
  closeEtoolPopsOutside(e)
  handleDocFormulaMousedown(e)
}

onMounted(() => {
  document.addEventListener('mouseup', handleGlobalMouseUp)
  document.addEventListener('selectionchange', handleGlobalSelectionChange)
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('click', handleGlobalClick)
  document.addEventListener('mousedown', handleDocMouseDown)
})

onUnmounted(() => {
  document.removeEventListener('mouseup', handleGlobalMouseUp)
  document.removeEventListener('selectionchange', handleGlobalSelectionChange)
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', handleGlobalClick)
  document.removeEventListener('mousedown', handleDocMouseDown)
  clearTimeout(loadTimer)
  clearTimeout(readerPosTimer)
  saveReaderPos()
  aiTitleTimers.forEach(t => clearTimeout(t))
  aiTitleTimers.clear()
})

function handleGlobalClick(e) {
  if (isTextDragOrSelect(e)) return
  toggleClozeSpan(e)
  // 点击 cloze 气泡外部时隐藏气泡
  if (clozeBubbleVisible.value && !e.target.closest('.cloze-bubble')) {
    hideClozeBubble()
  }
}
</script>

<style scoped>
.shell {
  flex: 1;
  min-width: 0;
  width: auto;
}

/* ===== Document View ===== */
.docview {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  position: relative;
}

.docview.loading .d-acts {
  opacity: 0.35;
}

.d-load {
  display: none;
  position: absolute;
  left: 0;
  right: 0;
  top: 52px;
  bottom: 0;
  background: var(--surface);
  z-index: 2;
  padding: 56px 72px 40px;
  overflow: hidden;
}

.docview.loading .d-load {
  display: block;
}

.d-load-inner {
  max-width: 740px;
  margin: 0 auto;
}

.d-load-hd {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
  color: var(--ink-3);
  font-size: 13px;
}

.d-spin {
  width: 16px;
  height: 16px;
  border: 2px solid var(--line);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex: 0 0 16px;
}

.skel {
  height: 13px;
  background: var(--line);
  border-radius: 6px;
  margin: 0 0 12px;
  background-image: linear-gradient(90deg, #e5e7ec 0%, #f5f6f8 50%, #e5e7ec 100%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease infinite;
}

.skel.h { height: 18px; width: 42%; margin-bottom: 16px; }
.skel.w1 { width: 100%; }
.skel.w2 { width: 92%; }
.skel.w3 { width: 78%; }
.skel.w4 { width: 64%; }
.skel.gap { margin-bottom: 28px; }

.d-top {
  height: 56px;
  flex: 0 0 56px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px 0 18px;
  border-bottom: 1px solid var(--line);
  position: relative;
  z-index: 50;
  overflow: hidden;
}

.d-file {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
}

.d-menu {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 2px 0 0;
  border: 0;
  background: transparent;
  color: var(--ink-2);
  font-size: 15px;
  font-weight: 600;
  line-height: 20px;
  cursor: pointer;
  flex: 0 0 auto;
  white-space: nowrap;
}

.d-menu .ic,
.d-menu .app-icon {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
}

.d-menu:hover {
  color: var(--ink);
}

.d-menu-div {
  width: 1px;
  height: 16px;
  background: var(--line);
  flex: 0 0 1px;
  margin: 0 4px 0 2px;
}

.d-back {
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-2);
}

.d-back:hover {
  background: var(--bg-soft);
  color: var(--ink);
}

.d-back svg {
  width: 20px;
  height: 20px;
}

.d-toc {
  height: 26px;
  padding: 0 10px;
  margin-left: 6px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ink);
  font-size: 13px;
  font-weight: 550;
  white-space: nowrap;
  cursor: pointer;
  flex: 0 0 auto;
}

.d-toc:hover {
  background: var(--bg-soft);
  border-color: var(--line-strong);
}

.d-toc.on {
  background: var(--accent-weak);
  border-color: var(--accent-weak-2);
  color: var(--accent-ink);
}

.d-file .fn {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.d-file .fm {
  font-size: 12.5px;
  font-weight: 500;
  color: var(--ink-3);
  white-space: nowrap;
  margin-left: 2px;
}

.d-acts {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  position: relative;
  z-index: 2;
}

.d-act {
  height: 40px;
  padding: 0 11px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 550;
  color: var(--ink-2);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

.d-act:hover {
  background: var(--bg-soft);
  color: var(--ink);
}

.d-act svg,
.d-act .app-icon {
  font-size: 24px;
  width: 24px;
  height: 24px;
  overflow: hidden;
  flex: 0 0 24px;
}

.d-act.pill {
  height: 40px;
  padding: 0 14px;
  border: 1.25px solid #D2D4DA;
  border-radius: 999px;
  background: #fff;
  color: var(--ink);
}

.d-act.pill:hover {
  background: var(--bg-soft);
  border-color: var(--line-strong);
}

.d-act.primary {
  background: var(--btn);
  color: #fff;
}

.d-act.primary:hover {
  background: var(--btn-hover);
}

.d-act.on {
  background: var(--accent-weak);
  color: var(--accent-ink);
}

.d-act.busy {
  opacity: 0.55;
  pointer-events: none;
}

.d-act:not(.primary)[disabled] {
  opacity: 0.36;
  pointer-events: none;
  background: transparent;
}

.d-act.primary[disabled],
.d-act.primary.busy {
  background: #b0b3ba;
  color: #fff;
  opacity: 1;
  pointer-events: none;
  cursor: not-allowed;
}

.d-act-spin {
  width: 14px;
  height: 14px;
  flex: 0 0 14px;
  border-color: rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
}

.d-act.warn {
  color: var(--danger);
}

.d-act.warn:hover {
  background: #fdeeee;
}

.d-page {
  flex: 1;
  overflow: auto;
  padding: 40px 24px 80px;
}

.d-inner {
  margin: 0 auto;
}

/* ===== Section / KB Flip ===== */
.d-spacer {
  width: 100%;
  pointer-events: none;
}

.d-sec {
  margin: 0 0 28px;
  width: 100%;
  box-sizing: border-box;
  cursor: pointer;
  border-radius: 12px;
  padding: 10px 14px;
  overflow: hidden;
  transition: background 0.15s;
  user-select: text;
  -webkit-user-select: text;
}

.d-sec:first-child {
  margin-top: 4px;
}

.d-sec h2 {
  font-size: 17px;
  font-weight: 650;
  margin: 0 0 10px;
  letter-spacing: -0.01em;
  cursor: text;
}

.d-sec p {
  font-size: 16px;
  line-height: 1.85;
  color: var(--ink);
  margin: 0 0 0.85em;
  cursor: text;
}

.d-sec:hover {
  background: var(--bg-plain);
}

.kb-front {
  display: none;
}

.d-sec.flipped {
  width: 100%;
  background: var(--surface);
  outline: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(20, 30, 60, 0.06);
  cursor: pointer;
}

.d-sec.flipped:hover {
  background: var(--surface);
}

.d-sec.flipped .kb-front {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 12px 16px 14px;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
}

.d-sec.flipped .kb-front * {
  user-select: none;
  -webkit-user-select: none;
}

.d-sec.flipped .kb-q[contenteditable="true"] {
  user-select: text;
  -webkit-user-select: text;
}

.d-sec.flipped .kb-back {
  display: none;
}

.d-sec.flipped.compact .kb-front {
  padding: 8px 16px;
  justify-content: center;
}

.d-sec.flipped.compact .kb-mid {
  padding: 4px;
}

.kb-bar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-height: 26px;
}

.kb-ai {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: #fff;
  color: var(--ink);
  font-size: 13px;
  font-weight: 500;
  border: 1px solid var(--line);
}

.kb-ai .ic {
  width: 14px;
  height: 14px;
  flex: 0 0 14px;
}

.kb-ai:hover {
  background: var(--bg-soft);
}

.kb-ai:disabled,
.kb-ai.busy {
  cursor: not-allowed;
  color: var(--ink-3);
  background: #fff;
  pointer-events: none;
}


.kb-mid {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 6px;
  flex: 1;
  padding: 8px 4px;
}

.kb-title-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 72px;
  max-width: 86%;
}

.kb-q {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.04em;
  line-height: 1.3;
  color: var(--ink);
  outline: none;
  min-width: 2em;
  text-align: center;
  word-break: break-word;
}

.kb-q.generating {
  color: var(--ink-3);
}

.kb-edit.locked {
  color: var(--ink-4);
}

.kb-line {
  display: none;
  width: 100%;
  min-width: 72px;
  height: 1px;
  background: var(--ink-2);
  margin-top: 7px;
  border-radius: 1px;
}

.kb-title-wrap.editing .kb-line {
  display: block;
}

.kb-edit-wrap {
  display: flex;
  flex-shrink: 0;
}

.kb-edit {
  color: var(--ink-3);
  padding: 0 0 1px;
  display: flex;
  flex-shrink: 0;
}

.kb-edit:hover,
.kb-edit.on {
  color: var(--ink-2);
}

.kb-edit.on {
  color: var(--accent);
}

.kb-hint {
  font-size: 13.5px;
  color: var(--ink-3);
  text-align: center;
  padding-top: 4px;
}

.eye-fab {
  position: absolute;
  right: 20px;
  bottom: 24px;
  width: 48px;
  height: 48px;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: #7C838C;
  z-index: 8;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.eye-fab:hover {
  color: #5f666e;
  background: transparent;
}

.eye-fab svg,
.eye-fab .app-icon {
  width: 48px;
  height: 48px;
}

.eye-off {
  display: none;
}

.eye-fab.revealed .eye-on {
  display: none;
}

.eye-fab.revealed .eye-off {
  display: inline-flex;
}

.docview.loading .eye-fab {
  display: none;
}

/* ===== Edit View ===== */
.editview {
  display: none;
  flex: 1;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  background: var(--bg);
  position: relative;
}

.shell.editing .docview {
  display: none;
}

.shell.editing .editview {
  display: flex;
}

.editview.ai-lock .eblk-txt {
  pointer-events: none;
  user-select: none;
  caret-color: transparent;
}

.e-page {
  flex: 1;
  overflow: auto;
  min-height: 0;
  padding: 28px 72px 120px;
}

.e-inner {
  max-width: 740px;
  margin: 0 auto;
}

.e-top {
  height: 56px;
  flex: 0 0 56px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px 0 18px;
  border-bottom: 1px solid var(--line);
  background: var(--surface);
}

.e-top .fn {
  font-size: 13.5px;
  font-weight: 600;
  flex: 0 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.e-top-acts {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  margin-left: auto;
}

.e-batch-acts {
  display: none;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  margin-left: auto;
}

.shell.editing.batch .e-top-acts {
  display: none;
}

.shell.editing.batch .e-batch-acts {
  display: flex;
}

.e-batch-acts .d-act.merge {
  background: transparent;
  color: var(--ink);
  font-weight: 600;
}

.e-batch-acts .d-act.merge:hover {
  background: transparent;
  color: var(--ink);
}

.e-batch-acts .d-act.merge[disabled] {
  color: var(--ink-3);
  opacity: 1;
  pointer-events: none;
  background: transparent;
}

/* ===== Editor Toolbar ===== */
.etool {
  flex: 0 0 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-plain);
  border-bottom: 1px solid var(--line);
  position: relative;
  z-index: 6;
  overflow: visible;
  transition: height 0.22s var(--ease), flex-basis 0.22s var(--ease), border-width 0.22s var(--ease), opacity 0.18s var(--ease);
}

.shell.editing.batch .etool {
  height: 0;
  flex-basis: 0;
  border-bottom-width: 0;
  opacity: 0;
  pointer-events: none;
  overflow: hidden;
}

.etool-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.etool-div {
  width: 1px;
  height: 16px;
  background: var(--line-strong);
  margin: 0 8px;
  flex: 0 0 1px;
}

.etb {
  height: 40px;
  min-width: 40px;
  padding: 0 7px;
  border-radius: 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  color: var(--ink-2);
  position: relative;
  cursor: pointer;
  flex: 0 0 auto;
}

.etb:hover {
  background: var(--line);
}

.etb.on {
  background: var(--line-strong);
  color: var(--ink);
}

.etb.off {
  color: #c9c9c9;
  pointer-events: none;
}

.etb svg,
.etb .app-icon {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
}

.etb .tx {
  font-size: 12.5px;
  font-weight: 500;
  white-space: nowrap;
  line-height: 1;
}

.etb-style {
  min-width: 52px;
  padding: 0 8px;
  gap: 4px;
}

.etb.open .chev {
  transform: rotate(180deg);
}

.etb .chev {
  width: 10px;
  height: 10px;
  flex: 0 0 10px;
  opacity: 0.5;
  transition: transform 0.15s var(--ease);
}

.etb-pop {
  display: none;
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  background: var(--surface);
  border-radius: 10px;
  box-shadow: 0 10px 28px rgba(20, 30, 60, 0.16);
  padding: 6px;
  min-width: 148px;
  z-index: 8;
  border: 1px solid var(--line);
}

.etb.open > .etb-pop {
  display: block;
}

.etb-file {
  display: none;
}

.etb-opt {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  padding: 0 10px;
  border-radius: 7px;
  font-size: 13px;
  color: var(--ink);
  width: 100%;
  text-align: left;
}

.etb-opt:hover {
  background: var(--bg-soft);
}

.etb-opt.cur {
  background: var(--bg-soft);
  color: var(--accent);
}

.etb-style-pop {
  width: 228px;
  min-width: 228px;
  padding: 6px;
}

.etb-style-pop .etb-opt {
  height: 40px;
  gap: 10px;
  padding: 0 10px;
  border-radius: 8px;
  font-size: 14px;
}

.etb-style-pop .si {
  width: 22px;
  flex: 0 0 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
}

.etb-style-pop .etb-opt.cur .si {
  color: var(--accent);
}

.etb-style-pop .sn {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  text-align: left;
}

.etb-style-pop .sk {
  width: 16px;
  flex: 0 0 16px;
  opacity: 0;
}

.etb-style-pop .etb-opt.cur .sk {
  opacity: 1;
  color: var(--accent);
}

.etb-swatches {
  display: flex;
  gap: 6px;
  padding: 6px 8px;
}

.etb-swatches i {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.08);
  cursor: pointer;
}

.etb.insert {
  color: var(--accent-ink);
}

/* ===== Edit Blocks ===== */
.eblk {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  min-width: 0;
  max-width: 100%;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 16px;
  margin: 0 0 14px;
  box-shadow: 0 4px 14px rgba(20, 30, 60, 0.05);
  transition: transform 0.15s ease;
}

.eblk.drag-over {
  margin-top: 48px;
  position: relative;
}

.eblk.drag-over::before {
  content: '';
  position: absolute;
  top: -28px;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent);
  border-radius: 2px;
}

.eblk-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 0 0 28px;
  padding-top: 2px;
  position: relative;
}

.eblk-handle {
  width: 28px;
  height: 22px;
  color: var(--ink-4);
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eblk-split {
  height: 22px;
  padding: 0 2px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-2);
  line-height: 1;
  white-space: nowrap;
}

.eblk-split:hover,
.eblk.open-split .eblk-split {
  background: var(--accent-weak);
  color: var(--accent);
}

.eblk-del {
  height: 22px;
  padding: 0 2px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  color: var(--danger);
  line-height: 1;
  white-space: nowrap;
  background: transparent;
}

.eblk-del:hover {
  background: rgba(210, 67, 57, 0.08);
  color: var(--danger);
}

.eblk-split-pop {
  display: none;
  position: absolute;
  left: calc(100% + 6px);
  top: 22px;
  z-index: 12;
  min-width: 148px;
  padding: 6px;
  background: var(--surface);
  border-radius: 10px;
  box-shadow: 0 10px 28px rgba(20, 30, 60, 0.16);
  border: 1px solid var(--line);
}

.eblk.open-split .eblk-split-pop {
  display: block;
}

.eblk-split-opt {
  display: block;
  width: 100%;
  text-align: left;
  height: 34px;
  padding: 0 10px;
  border-radius: 7px;
  font-size: 13px;
  color: var(--ink);
}

.eblk-split-opt:hover {
  background: var(--bg-soft);
}

.shell.editing.batch .eblk-split,
.shell.editing.batch .eblk-split-pop,
.shell.editing.batch .eblk-del {
  display: none !important;
}

.eblk-check {
  display: none;
  position: relative;
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
  margin-top: 4px;
  cursor: pointer;
}

.shell.editing.batch .eblk-check {
  display: block;
}

.eblk-check input {
  position: absolute;
  inset: -4px;
  margin: 0;
  opacity: 0;
  cursor: pointer;
  width: 26px;
  height: 26px;
}

.eblk-check i {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: 1.5px solid #8f96e0;
  border-radius: 4px;
  background: var(--surface);
  pointer-events: none;
}

.eblk-check i svg {
  width: 11px;
  height: 11px;
  stroke: #fff;
  fill: none;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: 0;
}

.eblk-check input:checked + i {
  background: var(--accent);
  border-color: var(--accent);
}

.eblk-check input:checked + i svg {
  opacity: 1;
}

.shell.editing.batch .eblk {
  outline: 1.5px solid #c3c9ff;
}

.shell.editing.batch .eblk.picked {
  outline-color: var(--accent);
  background: var(--accent-tint);
}

.eblk-txt {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  min-height: 2em;
  overflow-x: auto;
  font-size: 15.5px;
  line-height: 1.8;
  color: var(--ink);
  outline: none;
}

.shell.brush-on .eblk-txt,
.shell.brush-on .eblk-txt * {
  cursor: crosshair;
}

.eblk-txt .math {
  cursor: pointer;
}
.eblk-txt .math:hover {
  opacity: 0.85;
}

.eblk-txt:focus {
  background: var(--bg-plain);
}

/* 表格块：内嵌 vditor（即时渲染，markdown 双向） */
.eblk-txt.vt {
  padding: 0;
  min-height: 140px;
  background: transparent;
}

.eblk-txt.vt :deep(.vditor) {
  border-radius: 8px;
  border-color: var(--line);
  background: var(--surface);
}

.eblk-txt.vt :deep(.vditor) .vditor-ir {
  padding: 10px 14px;
  font-size: 15px;
  line-height: 1.8;
}

.eblk-txt.vt :deep(.vditor) .vditor-ir table {
  width: auto;
}

.eblk-txt.vt :deep(.vditor) .vditor-ir pre.vditor-reset>code {
  font-size: 13px;
}

.eblk-txt.vt :deep(.vditor) .vditor-content .vditor-sv,
.eblk-txt.vt :deep(.vditor) .vditor-content .vditor-wysiwyg {
  padding: 10px 14px;
  font-size: 15px;
  line-height: 1.8;
}

.eblk-txt.vt :deep(.vditor) .vditor-toolbar--bottom {
  display: none;
}

.eblk-txt :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 10px;
  letter-spacing: -0.02em;
}

.eblk-txt :deep(h2) {
  font-size: 18px;
  font-weight: 650;
  margin: 0 0 8px;
}

.eblk-txt :deep(h3) {
  font-size: 16px;
  font-weight: 650;
  margin: 0 0 6px;
  color: var(--ink-2);
}

.eblk-txt :deep([data-user-unbold]) {
  font-weight: 400;
}

.eblk-txt :deep(p) {
  margin: 0 0 0.6em;
}

.eblk-txt :deep(p:last-child) {
  margin: 0;
}

.eblk-txt :deep(ol),
.eblk-txt :deep(ul) {
  margin: 0 0 0.6em;
  padding-left: 1.4em;
}

.eblk-txt :deep(li) {
  margin: 0 0 0.2em;
}

.eblk.ai-new {
  animation: aiBlkIn 0.38s ease;
}

/* ===== AI Cloze Pick ===== */
.ai-cloze-pick {
  display: none;
  position: fixed;
  z-index: 820;
  min-width: 168px;
  padding: 6px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: 0 10px 28px rgba(20, 30, 60, 0.16);
}

.ai-cloze-pick.on {
  display: block;
}

.ai-cloze-pick button {
  display: flex;
  align-items: center;
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 550;
  color: var(--ink);
  text-align: left;
}

.ai-cloze-pick button:hover {
  background: var(--bg-soft);
}

.ai-confirm {
  position: fixed;
  inset: 0;
  z-index: 860;
  display: none;
  align-items: center;
  justify-content: center;
}

.ai-confirm.on {
  display: flex;
}

.ai-confirm-scrim {
  position: absolute;
  inset: 0;
  background: rgba(22, 24, 29, 0.36);
}

.ai-confirm-card {
  position: relative;
  z-index: 1;
  width: 320px;
  max-width: calc(100% - 48px);
  background: var(--surface);
  border-radius: 18px;
  padding: 28px 0 0;
  box-shadow: 0 16px 40px rgba(20, 30, 60, 0.16);
  text-align: center;
}

.ai-confirm-txt {
  margin: 0 24px 22px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.65;
  color: var(--ink);
}

.ai-confirm-acts {
  display: flex;
  border-top: 1px solid var(--line);
}

.ai-confirm-cancel,
.ai-confirm-ok {
  flex: 1;
  height: 48px;
  border-radius: 0;
  background: transparent;
  font-size: 15px;
  font-weight: 550;
}

.ai-confirm-cancel {
  color: var(--ink);
}

.ai-confirm-cancel:hover {
  background: var(--bg-soft);
}

.ai-confirm-ok {
  color: var(--accent);
  font-weight: 650;
  border-left: 1px solid var(--line);
}

.ai-confirm-ok:hover {
  background: var(--accent-weak);
}

/* ===== Cloze Bubble ===== */
.cloze-bubble {
  position: fixed;
  z-index: 810;
  display: flex;
  align-items: center;
  height: 40px;
  padding: 0 4px;
  background: var(--ink);
  border-radius: 10px;
  box-shadow: 0 10px 28px rgba(20, 30, 60, 0.28);
  color: #eaebed;
  user-select: none;
  visibility: hidden;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s var(--ease);
}

.cloze-bubble.on {
  visibility: visible;
  opacity: 1;
  pointer-events: auto;
}

.cloze-bubble::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -4px;
  width: 8px;
  height: 8px;
  margin-left: -4px;
  background: var(--ink);
  transform: rotate(45deg);
}

.cloze-bubble.below::after {
  top: -4px;
  bottom: auto;
}

.cloze-bubble button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 14px;
  border-radius: 7px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.cloze-bubble button:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* ===== Selection Toolbar ===== */
.selbar {
  position: fixed;
  z-index: 800;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  width: max-content;
  height: 40px;
  padding: 0 4px;
  gap: 0;
  overflow: visible;
  background: var(--ink);
  border-radius: 10px;
  box-shadow: 0 10px 28px rgba(20, 30, 60, 0.28);
  color: #eaebed;
  user-select: none;
  white-space: nowrap;
  visibility: hidden;
  opacity: 0;
  pointer-events: none;
}

.selbar.on {
  visibility: visible;
  opacity: 1;
  pointer-events: auto;
}

.selbar::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -4px;
  width: 8px;
  height: 8px;
  margin-left: -4px;
  background: var(--ink);
  transform: rotate(45deg);
}

.selbar.below::after {
  top: -4px;
  bottom: auto;
}

.selbar-item {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 40px;
  padding: 0 9px;
  color: #eaebed;
  border-radius: 7px;
  position: relative;
  flex: 0 0 auto;
  cursor: pointer;
}

.selbar-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.selbar-item.on {
  background: rgba(79, 92, 231, 0.45);
}

.selbar-item .app-icon {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  color: inherit;
}

.selbar-item .lb {
  font-size: 12px;
  line-height: 1;
  color: #eaebed;
}

.selbar-item.cloze-act {
  color: #c3c9ff;
}

.selbar-div {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.18);
  margin: 0 3px;
  flex: 0 0 1px;
}

.selbar-pop {
  display: none;
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  min-width: 112px;
  background: var(--surface);
  border-radius: 12px;
  padding: 6px;
  z-index: 3;
  box-shadow: 0 12px 32px rgba(20, 30, 60, 0.18);
  white-space: normal;
}

.selbar-pop.style-drawer {
  width: 228px;
  padding: 6px;
}

.selbar-item.open > .selbar-pop {
  display: block;
}

.selbar-opt {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 40px;
  padding: 0 10px;
  border-radius: 8px;
  color: var(--ink);
  cursor: pointer;
}

.selbar-opt:hover {
  background: var(--bg-plain);
}

.selbar-opt.cur {
  background: var(--bg-soft);
  color: var(--accent);
}

.selbar-opt .si {
  width: 22px;
  flex: 0 0 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
}

.selbar-opt.cur .si {
  color: var(--accent);
}

.selbar-opt .sn {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.selbar-opt .sk {
  width: 16px;
  flex: 0 0 16px;
  opacity: 0;
}

.selbar-opt.cur .sk {
  opacity: 1;
  color: var(--accent);
}

.selbar-swatches {
  display: flex;
  gap: 6px;
  padding: 4px 6px;
}

.selbar-swatches i {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: block;
  border: 1px solid rgba(0, 0, 0, 0.08);
  cursor: pointer;
}



.cloze.shown:hover {
  background: var(--accent-weak);
}

/* ===== Blk image ===== */
:deep(.blk-img) {
  margin: 0;
  padding: 0;
  max-width: 100%;
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-soft);
  border: 1px solid var(--line);
}

:deep(.blk-img img) {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  max-height: min(70vh, 560px);
  object-fit: contain;
}

.eblk-txt :deep(img),
.kb-back :deep(img) {
  display: block;
  max-width: 100%;
  height: auto;
  max-height: min(70vh, 560px);
  object-fit: contain;
}

/* ===== Pagebreak ===== */
.pagebreak {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 8px 0 32px;
  color: var(--ink-3);
  font-size: 12px;
  letter-spacing: 0.06em;
  user-select: none;
  pointer-events: none;
}

.pagebreak::before,
.pagebreak::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--line);
}

/* ===== TOC Panel ===== */
.toc-panel {
  position: absolute;
  top: 52px;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--surface);
  border-right: 1px solid var(--line);
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.08);
  z-index: 100;
  display: flex;
  flex-direction: column;
  visibility: hidden;
  opacity: 0;
  transition: visibility 0.22s, opacity 0.22s var(--ease);
}

.toc-panel.on {
  visibility: visible;
  opacity: 1;
}

.toc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--line);
  flex: 0 0 auto;
}

.toc-title {
  font-size: 16px;
  font-weight: 650;
  color: var(--ink);
}

.toc-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-3);
}

.toc-close:hover {
  background: var(--bg-soft);
  color: var(--ink);
}

.toc-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.toc-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s;
}

.toc-item:hover {
  background: var(--bg-soft);
}

/* 当前正在读的章节：常驻灰色高亮（与悬停同色） */
.toc-item.active {
  background: var(--bg-soft);
}

.toc-item-ic {
  flex: 0 0 14px;
  color: var(--ink-4);
}

.toc-item-name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  font-weight: 400;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toc-loading,
.toc-nomore,
.toc-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 16px;
  font-size: 13px;
  color: var(--ink-3);
}

.toc-spin {
  width: 14px;
  height: 14px;
  border: 2px solid var(--line);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: toc-spin 0.6s linear infinite;
}

@keyframes toc-spin {
  to { transform: rotate(360deg); }
}

</style>

<style>
/* 挖空标签基础样式（字重由 .docview / .editview 分别覆盖） */
customclickablespan {
  display: inline;
  border-bottom: 2px dashed var(--cloze);
  background: transparent;
  padding: 0 1px;
  border-radius: 0;
  color: inherit;
  font-weight: inherit;
  line-height: inherit;
  vertical-align: baseline;
  user-select: none;
  cursor: pointer;
  transition: background 0.15s var(--ease);
  word-break: break-all;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}

customclickablespan.shown {
  color: inherit;
  background: transparent;
  border-bottom: 2px dashed var(--cloze);
  font-weight: inherit;
}

/* 阅读态：挖空文字一律加粗（与编辑页是否加粗无关），且可拖拽选中 */
.docview customclickablespan {
  font-weight: 700 !important;
  user-select: text;
  -webkit-user-select: text;
}

.docview customclickablespan * {
  user-select: text;
  -webkit-user-select: text;
}

.docview customclickablespan.shown {
  font-weight: 700 !important;
}

.docview customclickablespan.shown * {
  font-weight: inherit !important;
}

/* 阅读模式（仅 .docview）：隐藏挖空时强制子元素透明，避免内联样式覆盖 */
.docview customclickablespan:not(.shown),
.docview customclickablespan:not(.shown) * {
  color: transparent !important;
  text-decoration: none !important;
  -webkit-text-decoration: none !important;
}

/* 阅读模式：显示时恢复子元素自然颜色（内联样式可覆盖） */
.docview customclickablespan.shown * {
  color: unset;
  text-decoration: unset;
}

customclickablespan:hover {
  background: var(--accent-weak);
}

/* 非 scoped: markdown 渲染块（.md-block）经 innerHTML 动态渲染，scoped CSS 不生效 */
.md-block > :first-child {
  margin-top: 0;
}

.md-block > :last-child {
  margin-bottom: 0;
}

.md-block table {
  width: 100%;
  border-collapse: collapse;
  margin: 6px 0;
  font-size: 13px;
  line-height: 1.6;
}

.md-block th,
.md-block td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
  word-break: break-word;
}

.md-block th {
  background: var(--bg-soft);
  font-weight: 700;
}

/* 非 scoped: .e-cloze 也是动态创建的元素，scoped CSS 不生效 */
.e-cloze {
  display: inline;
  background: transparent;
  border-bottom: 2px dashed var(--cloze);
  padding: 0 1px;
  border-radius: 0;
  color: inherit;
  font-weight: inherit;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}

.docview .e-cloze {
  font-weight: 700 !important;
}

.e-cloze.ai-new {
  animation: aiClozeIn 0.45s ease;
}

/* 编辑模式下挖空文字始终可见、可编辑（字重由内容 <b> 等标记控制，可取消加粗） */
.editview customclickablespan,
.editview customclickablespan.shown,
.shell.editing .editview customclickablespan,
.shell.editing .editview customclickablespan.shown {
  opacity: 1 !important;
  visibility: visible !important;
  user-select: text;
  -webkit-user-select: text;
  cursor: text;
}

.editview customclickablespan *,
.editview customclickablespan.shown *,
.shell.editing .editview customclickablespan *,
.shell.editing .editview customclickablespan.shown * {
  opacity: 1 !important;
  visibility: visible !important;
  user-select: text;
  -webkit-user-select: text;
}

.editview u,
.editview customclickablespan u {
  text-decoration-line: underline !important;
  -webkit-text-decoration-line: underline !important;
  text-decoration-style: solid !important;
  text-decoration-color: #222 !important;
  text-decoration-thickness: 2px !important;
  text-underline-offset: 2px;
  border-bottom: none !important;
}

.editview s,
.editview strike,
.editview del,
.editview customclickablespan s,
.editview customclickablespan strike,
.editview customclickablespan del {
  text-decoration-line: line-through !important;
  -webkit-text-decoration-line: line-through !important;
  text-decoration-style: solid !important;
  text-decoration-color: #222 !important;
  text-decoration-thickness: 2px !important;
}

/* ---- 公式编辑器浮层 ---- */
.me-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: transparent;
}

.math-editor {
  position: fixed;
  z-index: 61;
  width: 460px;
  max-width: calc(100vw - 24px);
  box-sizing: border-box;
  padding: 14px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(20, 30, 60, 0.18);
}

.me-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 10px;
}

.me-delim {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px;
  font-weight: 400;
  color: var(--ink-2);
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 2px 7px;
}

.me-input {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
  min-height: 72px;
  max-height: 220px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--ink);
  background: var(--bg);
  outline: none;
}

.me-input:focus {
  border-color: var(--accent);
}

.me-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-bottom: 8px;
  padding: 6px 8px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: 8px;
  align-items: center;
  user-select: none;
}
.me-tb-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--ink);
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.12s;
  font-family: 'Times New Roman', Times, serif;
}
.me-tb-btn:hover {
  background: var(--bg);
}
.me-tb-btn:active {
  background: var(--line);
}
.me-tb-btn sup,
.me-tb-btn sub {
  font-size: 10px;
  line-height: 1;
}
.me-tb-frac {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  font-size: 10px;
  line-height: 1.15;
}
.me-tb-frac i {
  font-style: normal;
  padding: 0 3px;
}
.me-tb-frac i + i {
  border-top: 1px solid currentColor;
}
.me-tb-split {
  display: inline-block;
  width: 1px;
  height: 18px;
  background: var(--line);
  margin: 0 3px;
}

.me-preview {
  margin-top: 10px;
  border: 1px dashed var(--line);
  border-radius: 8px;
  padding: 12px 14px;
  min-height: 44px;
  text-align: center;
  background: var(--bg-soft);
  overflow-x: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}

.me-err {
  color: #d5483e;
  font-size: 12px;
}

.me-btns {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.me-btn {
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
  border-radius: 8px;
  padding: 6px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.me-btn:hover {
  background: var(--bg-soft);
}

.me-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.me-btn.primary:hover {
  filter: brightness(1.06);
}
</style>
