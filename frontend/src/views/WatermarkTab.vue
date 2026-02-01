<template>
  <div class="panel main-layout watermark-panel">
    <div class="main-row">
    <aside class="pane-settings" aria-label="功能设置">
      <section class="section-card">
        <h3 class="section-title"><span class="icon-wrap"><Image :size="16" /></span>水印图片（支持静态/动态图）</h3>
        <div class="btn-text-row">
          <button type="button" class="secondary" @click="pickWatermark">选择图片</button>
          <span class="selection-display">{{ watermarkPath ? watermarkPath.replace(/^.*[\\/]/, '') : '请选择水印图片' }}</span>
        </div>
        <h3 class="section-title pos-title"><span class="icon-wrap"><SlidersHorizontal :size="16" /></span>水印不透明度（默认100%）</h3>
        <div class="opacity-row">
          <input v-model.number="opacityPercent" type="range" min="10" max="100" class="opacity-slider" />
          <input v-model.number="opacityPercent" type="number" min="10" max="100" class="opacity-num" />
          <span class="opacity-unit">%</span>
        </div>
        <h3 class="section-title pos-title"><span class="icon-wrap"><LayoutGrid :size="16" /></span>水印位置</h3>
        <div class="position-grid">
          <button
            v-for="item in positionOptions"
            :key="item.value"
            type="button"
            class="position-btn"
            :class="{ 'position-btn-active': position === item.value }"
            @click="position = item.value"
          >{{ item.label }}</button>
        </div>
        <h3 class="section-title pos-title"><span class="icon-wrap"><FolderOpen :size="16" /></span>输出目录（输出保持原命名）</h3>
        <div class="btn-text-row">
          <button type="button" class="secondary" @click="pickOutputDir">浏览</button>
          <span class="selection-display">{{ outputDir || '请选择输出目录' }}</span>
        </div>
      </section>
    </aside>
    <aside class="pane-video-list" aria-label="视频列表">
      <h2 class="pane-title"><span class="icon-wrap"><Video :size="16" /></span>视频列表</h2>
        <div
          class="drop-zone"
          :class="{ 'drop-zone-active': dropActive }"
          @dragover.prevent="dropActive = true"
          @dragleave.prevent="dropActive = false"
          @drop.prevent="onDrop"
        >
          <p class="drop-zone-text">拖拽视频文件到这里</p>
          <button type="button" class="primary drop-zone-btn" @click="openVideoDialog">选择视频文件</button>
        </div>
        <div class="video-list-wrap">
          <ul v-if="videoList.length" class="video-list" role="list">
            <li
              v-for="(item, i) in videoList"
              :key="item.path + String(i)"
              class="video-list-item"
            >
              <span class="video-list-filename" :title="item.path">{{ filename(item.path) }}</span>
              <span class="video-list-status" :class="'status-' + item.status">{{ statusText(item.status) }}</span>
            </li>
          </ul>
          <p v-else class="video-list-empty">暂无视频，请拖入或选择</p>
        </div>
    </aside>
    </div>
    <section class="section-card watermark-footer">
      <div class="watermark-actions">
        <button class="secondary" @click="reset">重置</button>
      </div>
    </section>
    <Teleport to="body">
      <div v-if="doneModalOpen" class="dialog-overlay" role="dialog" aria-modal="true" aria-labelledby="done-dialog-title-wm" @click.self="closeDoneModal">
        <div class="dialog-box done-dialog">
          <h2 id="done-dialog-title-wm" class="dialog-title">处理完成</h2>
          <p class="done-dialog-msg">{{ doneModalMsg }}</p>
          <button type="button" class="primary" @click="closeDoneModal">确定</button>
        </div>
      </div>
    </Teleport>
    <Teleport to="body">
      <VideoImportDialog
        :show="videoDialogOpen"
        @close="closeVideoDialog"
        @add-files="handleAddFiles"
        @add-folder="handleAddFolder"
      />
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { Video, Image, FolderOpen, SlidersHorizontal, LayoutGrid } from 'lucide-vue-next'
import { watermarkStream } from '../api'
import { openFile, openDir, IMAGE_FILTER } from '../dialog'
import { useVideoImport } from '../composables/useVideoImport'
import VideoImportDialog from '../components/VideoImportDialog.vue'

const tabState = inject('tabState')

const positionOptions = [
  { label: '左上', value: 'top_left' }, { label: '上', value: 'top' }, { label: '右上', value: 'top_right' },
  { label: '左', value: 'left' }, { label: '中', value: 'center' }, { label: '右', value: 'right' },
  { label: '左下', value: 'bottom_left' }, { label: '下', value: 'bottom' }, { label: '右下', value: 'bottom_right' },
]

const logLines = ref([])
function log(msg) {
  const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logLines.value.push(`[${ts}] ${msg}`)
}

const {
  videoList,
  inputPaths,
  videoDialogOpen,
  openVideoDialog,
  closeVideoDialog,
  dropActive,
  onDrop,
  handleAddFiles,
  handleAddFolder,
  filename,
  statusText,
  registerAppDrop,
  clearVideoList,
} = useVideoImport({ onLog: log })

const watermarkPath = ref('')
const outputDir = ref('')
const opacityPercent = ref(100)
const position = ref('center')
const processing = ref(false)
const progress = ref(0)
const doneModalOpen = ref(false)
const doneModalMsg = ref('')
let unlistenDrop = null

onMounted(() => {
  tabState.start = start
  const stopWatch = watch(() => processing.value, (v) => { tabState.processing = v }, { immediate: true })
  const unreg = registerAppDrop()
  unlistenDrop = () => {
    stopWatch()
    unreg()
    tabState.start = null
    tabState.processing = false
  }
})
onUnmounted(() => {
  if (unlistenDrop) unlistenDrop()
})

const logText = computed(() => logLines.value.join('\n') || '[暂无日志]')

async function pickWatermark() {
  const path = await openFile({ filters: [IMAGE_FILTER] })
  if (path) watermarkPath.value = path
}

async function pickOutputDir() {
  const dir = await openDir()
  if (dir) outputDir.value = dir
}

function closeDoneModal() {
  doneModalOpen.value = false
}

async function start() {
  const paths = inputPaths.value
  if (!paths.length) {
    log('请先选择视频')
    return
  }
  if (!watermarkPath.value) {
    log('请选择水印图片')
    return
  }
  if (!outputDir.value) {
    log('请选择输出目录')
    return
  }
  const pct = Math.max(10, Math.min(100, Number(opacityPercent.value) || 100))
  opacityPercent.value = pct
  const opacity = pct / 100
  videoList.value.forEach(i => { i.status = 'processing' })
  processing.value = true
  progress.value = 0
  log('开始添加水印...')
  try {
    await watermarkStream(
      {
        input_paths: paths,
        output_dir: outputDir.value,
        watermark_path: watermarkPath.value,
        opacity,
        position: position.value,
      },
      (ev) => {
        if (ev.type === 'log') log(ev.msg)
        else if (ev.type === 'progress') progress.value = ev.value
        else if (ev.type === 'done') {
          progress.value = 100
          const results = ev.results || {}
          videoList.value.forEach((item) => {
            const r = results[item.path]
            if (r) item.status = r[0] ? 'success' : 'fail'
          })
          const ok = ev.ok_count ?? 0
          const fail = ev.fail_count ?? 0
          doneModalMsg.value = `成功 ${ok} 个，失败 ${fail} 个`
          if (ev.error) doneModalMsg.value += '\n' + ev.error
          doneModalOpen.value = true
        }
      }
    )
  } catch (e) {
    log('请求失败: ' + e.message)
    progress.value = 100
    videoList.value.forEach(i => { if (i.status === 'processing') i.status = 'fail' })
  }
  processing.value = false
}

function reset() {
  clearVideoList()
  watermarkPath.value = ''
  outputDir.value = ''
  opacityPercent.value = 100
  position.value = 'center'
  progress.value = 0
  logLines.value = []
}
</script>

<style scoped>
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
  display: flex;
  flex-direction: column;
  align-items: flex-start;
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
.pane-settings .section-card {
  width: 100%;
}
.btn-text-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}
.btn-text-row .selection-display {
  margin-top: 0;
}
.pos-title {
  margin-top: 14px;
}
.opacity-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}
.opacity-slider {
  flex: 1;
  min-width: 80px;
  max-width: 200px;
}
.opacity-num {
  width: 60px;
  min-width: 60px;
  padding: 6px 8px;
  text-align: right;
}
.opacity-unit {
  font-size: 14px;
  color: var(--fg-muted);
}
.position-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-top: 8px;
  max-width: 220px;
}
.position-btn {
  padding: 8px;
  font-size: 13px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--fg);
  cursor: pointer;
  transition: border-color var(--transition-fast), background-color var(--transition-fast);
}
.position-btn:hover {
  border-color: var(--fg-muted);
  background: var(--card-hover);
}
.position-btn-active {
  border-color: var(--primary);
  background: var(--primary-ghost);
  color: var(--primary);
}
.video-list-wrap {
  margin-top: 10px;
  max-height: 180px;
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
  justify-content: space-between;
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
.video-list-empty {
  margin: 0;
  padding: 16px 10px;
  font-size: 13px;
  color: var(--fg-muted);
  text-align: center;
}
.watermark-footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.watermark-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}
</style>
