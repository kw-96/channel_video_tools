<template>
  <div class="panel main-layout">
    <div class="main-row">
    <aside class="pane-settings" aria-label="功能设置">
      <section class="section-card">
        <h3 class="section-title"><span class="icon-wrap"><FolderOpen :size="16" /></span>输出设置</h3>
        <div class="btn-text-row">
          <button type="button" class="secondary" @click="pickOutputDir">浏览</button>
          <span class="selection-display">{{ outputDir || '请选择输出目录' }}</span>
        </div>
        <h3 class="section-title pos-title"><span class="icon-wrap"><SlidersHorizontal :size="16" /></span>处理参数</h3>
        <div class="form-row">
          <label>目标宽度</label>
          <input v-model.number="targetWidth" type="number" min="1" class="input-num" />
          <label>目标高度</label>
          <input v-model.number="targetHeight" type="number" min="1" class="input-num" />
          <label>填充颜色</label>
          <select v-model="padColor">
            <option value="black">black</option>
            <option value="white">white</option>
            <option value="gray">gray</option>
          </select>
        </div>
      </section>
    </aside>
    <aside class="pane-video-list" aria-label="视频列表">
      <h2 class="pane-title"><span class="icon-wrap"><FolderInput :size="16" /></span>视频列表</h2>
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
    <Teleport to="body">
      <VideoImportDialog
        :show="videoDialogOpen"
        @close="closeVideoDialog"
        @add-files="handleAddFiles"
        @add-folder="handleAddFolder"
      />
    </Teleport>
    <div class="actions-row">
      <button class="secondary" @click="reset">重置</button>
    </div>
    <Teleport to="body">
      <div v-if="doneModalOpen" class="dialog-overlay" role="dialog" aria-modal="true" aria-labelledby="done-dialog-title" @click.self="closeDoneModal">
        <div class="dialog-box done-dialog">
          <h2 id="done-dialog-title" class="dialog-title">处理完成</h2>
          <p class="done-dialog-msg">{{ doneModalMsg }}</p>
          <button type="button" class="primary" @click="closeDoneModal">确定</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { FolderInput, FolderOpen, SlidersHorizontal } from 'lucide-vue-next'
import { normalizeStream } from '../api'
import { openDir } from '../dialog'
import { useVideoImport } from '../composables/useVideoImport'
import VideoImportDialog from '../components/VideoImportDialog.vue'

const tabState = inject('tabState')

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

const outputDir = ref('')
const targetWidth = ref(1920)
const targetHeight = ref(1080)
const padColor = ref('black')
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
    log('请先选择视频文件')
    return
  }
  if (!outputDir.value) {
    log('请选择输出目录')
    return
  }
  videoList.value.forEach(i => { i.status = 'processing' })
  processing.value = true
  progress.value = 0
  log('开始规范化处理...')
  try {
    await normalizeStream(
      {
        input_paths: paths,
        output_dir: outputDir.value,
        target_width: targetWidth.value,
        target_height: targetHeight.value,
        pad_color: padColor.value,
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
  outputDir.value = ''
  targetWidth.value = 1920
  targetHeight.value = 1080
  padColor.value = 'black'
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
.actions-row {
  margin-top: 16px;
  flex-shrink: 0;
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
.input-num {
  width: 100px;
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
</style>
