<template>
  <div class="tab-settings">
    <section class="section-card" aria-label="功能设置">
      <h3 class="section-title">输出设置</h3>
      <div class="btn-text-row">
        <button type="button" class="secondary" @click="pickOutputDir">浏览</button>
        <span class="selection-display">{{ outputDir || '请选择输出目录' }}</span>
      </div>
      <h3 class="section-title pos-title">处理参数</h3>
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
import { normalizeStream } from '../api'
import { openDir } from '../dialog'

const tabState = inject('tabState')
const { videoList, inputPaths, filename, statusText, clearVideoList } = inject('videoImport')

const logLines = ref([])
function log(msg) {
  const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logLines.value.push(`[${ts}] ${msg}`)
}

const outputDir = ref('')
const targetWidth = ref(1920)
const targetHeight = ref(1080)
const padColor = ref('black')
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
.input-num {
  width: 88px;
}
</style>
