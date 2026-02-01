<template>
  <div class="panel main-layout">
    <div class="main-row">
    <aside class="pane-settings" aria-label="功能设置">
      <section class="section-card">
        <h3 class="section-title"><span class="icon-wrap"><Video :size="16" /></span>主体视频</h3>
        <div class="btn-text-row">
          <button type="button" class="secondary" @click="openVideoDialog('main')">选择视频</button>
          <span class="selection-display">{{ displayPath(mainVideo) || '请选择主体视频' }}</span>
        </div>
        <h3 class="section-title pos-title"><span class="icon-wrap"><ListOrdered :size="16" /></span>插入位置</h3>
        <div class="segmented" role="group" aria-label="插入位置">
          <button type="button" :class="{ active: insertPosition === 'head' }" @click="insertPosition = 'head'">片头</button>
          <button type="button" :class="{ active: insertPosition === 'tail' }" @click="insertPosition = 'tail'">片尾</button>
        </div>
        <h3 class="section-title pos-title"><span class="icon-wrap"><PlusCircle :size="16" /></span>插入视频</h3>
        <div class="btn-text-row">
          <button type="button" class="secondary" @click="openVideoDialog('insert')">选择视频</button>
          <span class="selection-display">{{ displayPath(insertVideo) || '请选择要插入的视频文件' }}</span>
        </div>
        <h3 class="section-title pos-title"><span class="icon-wrap"><FileOutput :size="16" /></span>输出路径</h3>
        <div class="btn-text-row">
          <button type="button" class="secondary" @click="pickOutputPath">另存为</button>
          <span class="selection-display">{{ outputPath || '请选择输出路径' }}</span>
        </div>
      </section>
    </aside>
    <aside class="pane-video-list" aria-label="视频列表">
      <h2 class="pane-title">视频列表</h2>
      <div class="video-list-wrap">
        <ul class="video-list" role="list">
          <li
            v-for="(item, i) in mergeVideoList"
            :key="'merge-' + i"
            class="video-list-item"
          >
            <span class="video-list-filename" :title="item.path">{{ item.path ? displayPath(item.path) : mergePlaceholders[i] }}</span>
            <span class="video-list-status" :class="'status-' + item.status">{{ statusText(item.status) }}</span>
          </li>
        </ul>
      </div>
    </aside>
    </div>
    <div class="actions-row">
      <button class="secondary" @click="reset">重置</button>
    </div>
    <Teleport to="body">
      <VideoImportDialog
        :show="videoDialogOpen"
        @close="closeVideoDialog"
        @add-files="handleAddFiles"
        @add-folder="handleAddFolder"
      />
    </Teleport>
    <Teleport to="body">
      <div v-if="doneModalOpen" class="dialog-overlay" role="dialog" aria-modal="true" aria-labelledby="done-dialog-title-merge" @click.self="closeDoneModal">
        <div class="dialog-box done-dialog">
          <h2 id="done-dialog-title-merge" class="dialog-title">处理完成</h2>
          <p class="done-dialog-msg">{{ doneModalMsg }}</p>
          <button type="button" class="primary" @click="closeDoneModal">确定</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { Video, PlusCircle, FileOutput, ListOrdered } from 'lucide-vue-next'
import { merge } from '../api'
import { saveFile } from '../dialog'
import { useSingleVideoDialog } from '../composables/useSingleVideoDialog'
import VideoImportDialog from '../components/VideoImportDialog.vue'

const tabState = inject('tabState')

const mainVideo = ref('')
const insertVideo = ref('')

function onVideoSelected(context, path) {
  if (context === 'main') mainVideo.value = path
  else if (context === 'insert') insertVideo.value = path
}

const {
  videoDialogOpen,
  openVideoDialog,
  closeVideoDialog,
  handleAddFiles,
  handleAddFolder,
} = useSingleVideoDialog(onVideoSelected)

function displayPath(p) {
  if (!p) return ''
  const idx = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'))
  return idx >= 0 ? p.slice(idx + 1) : p
}

const STATUS_MAP = { pending: '待处理', processing: '处理中', success: '成功', fail: '失败', empty: '待选择' }
function statusText(s) {
  return STATUS_MAP[s] || s
}

const outputPath = ref('')
const insertPosition = ref('head')
const processing = ref(false)
const progress = ref(0)
const mergeStatus = ref('pending')
const logLines = ref([])
const doneModalOpen = ref(false)
const doneModalMsg = ref('')

const mergePlaceholders = ['请选择主体视频', '请选择要插入的视频文件']
const mergeVideoList = computed(() => [
  { path: mainVideo.value, status: mainVideo.value ? mergeStatus.value : 'empty' },
  { path: insertVideo.value, status: insertVideo.value ? mergeStatus.value : 'empty' },
])

const logText = computed(() => logLines.value.join('\n') || '[暂无日志]')

let stopWatch = null
onMounted(() => {
  tabState.start = start
  stopWatch = watch(() => processing.value, (v) => { tabState.processing = v }, { immediate: true })
})
onUnmounted(() => {
  if (stopWatch) stopWatch()
  tabState.start = null
  tabState.processing = false
})

async function pickOutputPath() {
  const path = await saveFile()
  if (path) outputPath.value = path
}

function log(msg) {
  const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logLines.value.push(`[${ts}] ${msg}`)
}

function closeDoneModal() {
  doneModalOpen.value = false
}

async function start() {
  if (!mainVideo.value) {
    log('请选择主体视频')
    return
  }
  if (!insertVideo.value) {
    log('请选择插入视频')
    return
  }
  if (!outputPath.value) {
    log('请选择输出路径')
    return
  }
  processing.value = true
  progress.value = 0
  mergeStatus.value = 'processing'
  log('开始合并...')
  try {
    const res = await merge({
      main_video: mainVideo.value,
      insert_video: insertVideo.value,
      output_path: outputPath.value,
      insert_position: insertPosition.value,
    })
    if (res.ok) {
      log('合并完成')
      mergeStatus.value = 'success'
      doneModalMsg.value = '合并完成'
    } else {
      log(res.message || '合并失败')
      mergeStatus.value = 'fail'
      doneModalMsg.value = res.message || '合并失败'
    }
    doneModalOpen.value = true
  } catch (e) {
    log('请求失败: ' + e.message)
    mergeStatus.value = 'fail'
    doneModalMsg.value = '请求失败: ' + e.message
    doneModalOpen.value = true
  }
  progress.value = 100
  processing.value = false
}

function reset() {
  mainVideo.value = ''
  insertVideo.value = ''
  outputPath.value = ''
  insertPosition.value = 'head'
  mergeStatus.value = 'pending'
  progress.value = 0
  logLines.value = []
}
</script>

<style scoped>
.btn-text-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}
.btn-text-row .selection-display {
  margin-top: 0;
}
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
}
.main-row {
  display: flex;
  flex-direction: row;
  gap: 20px;
  flex: 1;
  min-height: 0;
}
.pane-settings {
  flex: 0 0 280px;
  min-width: 220px;
}
.pane-video-list {
  flex: 1;
  min-width: 260px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.pane-title {
  margin: 0 0 10px;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--fg);
}
.video-list-wrap {
  margin-top: 10px;
  max-height: 200px;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
}
.video-list {
  margin: 0;
  padding: 6px 0;
  list-style: none;
}
.video-list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  font-size: 13px;
  border-bottom: 1px solid var(--border);
}
.video-list-item:last-child {
  border-bottom: none;
}
.video-list-filename {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--fg);
}
.video-list-status {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}
.video-list-status.status-pending {
  background: var(--card-hover);
  color: var(--fg-muted);
}
.video-list-status.status-processing {
  background: var(--primary-ghost);
  color: var(--primary);
}
.video-list-status.status-success {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
.video-list-status.status-fail {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.video-list-status.status-empty {
  background: var(--card-hover);
  color: var(--fg-muted);
}
.actions-row {
  margin-top: 16px;
  flex-shrink: 0;
}
.pane-settings .section-card {
  width: 100%;
}
.pos-title {
  margin-top: 14px;
}
</style>
