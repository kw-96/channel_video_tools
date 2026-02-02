<template>
  <div class="tab-settings">
    <section class="section-card" aria-label="功能设置">
      <h3 class="section-title">输出目录（输出保持原命名）</h3>
      <div class="btn-text-row">
        <button type="button" class="secondary" @click="pickOutputDir">浏览</button>
        <span class="selection-display">{{ outputDir || '请选择输出目录' }}</span>
      </div>
      <h3 class="section-title pos-title">水印图片（支持静态/动态图）</h3>
      <div class="btn-text-row">
        <button type="button" class="secondary" @click="pickWatermark">选择图片</button>
        <span class="selection-display">{{ watermarkPath ? watermarkPath.replace(/^.*[\\/]/, '') : '请选择水印图片' }}</span>
      </div>
      <h3 class="section-title pos-title">水印不透明度（默认100%）</h3>
      <div class="opacity-row">
        <input v-model.number="opacityPercent" type="range" min="10" max="100" class="opacity-slider" />
        <input v-model.number="opacityPercent" type="number" min="10" max="100" class="opacity-num" />
        <span class="opacity-unit">%</span>
      </div>
      <h3 class="section-title pos-title">水印位置</h3>
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
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { watermarkStream } from '../api'
import { openFile, openDir, IMAGE_FILTER } from '../dialog'

const tabState = inject('tabState')
const { videoList, inputPaths, filename, statusText, clearVideoList } = inject('videoImport')

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


const watermarkPath = ref('')
const outputDir = ref('')
const opacityPercent = ref(100)
const position = ref('center')
const processing = ref(false)
const progress = ref(0)
const doneModalOpen = ref(false)
const doneModalMsg = ref('')
let stopWatch = null

onMounted(() => {
  tabState.start = start
  tabState.reset = reset
  stopWatch = watch(() => processing.value, (v) => { tabState.processing = v }, { immediate: true })
})
onUnmounted(() => {
  if (stopWatch) stopWatch()
  tabState.start = null
  tabState.reset = null
  tabState.processing = false
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
.tab-settings .section-card {
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
  width: 56px;
  min-width: 56px;
  padding: 5px 6px;
  text-align: right;
}
.opacity-unit {
  font-size: 12px;
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
  padding: 6px 12px;
  font-size: 12px;
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
</style>
