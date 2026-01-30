<template>
  <div class="panel">
    <section class="section">
      <h2 class="section-title">输入文件</h2>
      <p class="hint">每行一个路径，或使用下方多选（仅部分浏览器支持多选）</p>
      <textarea v-model="inputPathsText" rows="3" placeholder="输入视频路径，每行一个"></textarea>
      <input type="file" ref="fileInput" multiple accept="video/*" @change="onFileSelect" style="margin-top:8px" />
    </section>
    <section class="section">
      <h2 class="section-title">输出目录</h2>
      <input v-model="outputDir" type="text" placeholder="输出目录路径" class="full-width" />
    </section>
    <section class="section">
      <h2 class="section-title">处理参数</h2>
      <div class="row">
        <label>目标宽度</label>
        <input v-model.number="targetWidth" type="number" min="1" style="width:100px" />
        <label>目标高度</label>
        <input v-model.number="targetHeight" type="number" min="1" style="width:100px" />
        <label>填充颜色</label>
        <select v-model="padColor">
          <option value="black">black</option>
          <option value="white">white</option>
          <option value="gray">gray</option>
        </select>
      </div>
    </section>
    <section class="section">
      <button class="primary" :disabled="processing" @click="start">开始处理</button>
      <button class="secondary" @click="reset">重置</button>
    </section>
    <section class="section log">
      <h2 class="section-title">处理日志</h2>
      <pre class="log-text">{{ logText }}</pre>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { normalize } from '../api'

const inputPathsText = ref('')
const fileInput = ref(null)
const outputDir = ref('')
const targetWidth = ref(1920)
const targetHeight = ref(1080)
const padColor = ref('black')
const processing = ref(false)
const logLines = ref([])

const inputPaths = computed(() => {
  const t = inputPathsText.value.trim()
  if (!t) return []
  return t.split(/\n/).map(s => s.trim()).filter(Boolean)
})

const logText = computed(() => logLines.value.join('\n') || '[暂无日志]')

function log(msg) {
  const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logLines.value.push(`[${ts}] ${msg}`)
}

function onFileSelect(e) {
  const files = e.target.files
  if (!files?.length) return
  const paths = Array.from(files).map(f => f.path || f.name).filter(Boolean)
  if (paths.length) {
    inputPathsText.value = paths.join('\n')
    log(`已选择 ${paths.length} 个文件`)
  }
  e.target.value = ''
}

async function start() {
  const paths = inputPaths.value
  if (!paths.length) {
    log('请先输入或选择视频文件')
    return
  }
  if (!outputDir.value.trim()) {
    log('请填写输出目录')
    return
  }
  processing.value = true
  log('开始规范化处理...')
  try {
    const res = await normalize({
      input_paths: paths,
      output_dir: outputDir.value.trim(),
      target_width: targetWidth.value,
      target_height: targetHeight.value,
      pad_color: padColor.value,
    })
    if (res.ok) {
      log('全部处理完成')
    } else {
      for (const [path, arr] of Object.entries(res.results)) {
        if (!arr[0]) log(`${path}: ${arr[2]}`)
      }
    }
  } catch (e) {
    log('请求失败: ' + e.message)
  }
  processing.value = false
}

function reset() {
  inputPathsText.value = ''
  outputDir.value = ''
  targetWidth.value = 1920
  targetHeight.value = 1080
  padColor.value = 'black'
  logLines.value = []
}
</script>

<style scoped>
.panel { max-width: 800px; }
.section { margin-bottom: 16px; }
.section-title { margin: 0 0 8px; font-size: 0.95rem; }
.hint { margin: 0 0 4px; font-size: 0.85rem; color: var(--fg); opacity: 0.8; }
.full-width { width: 100%; }
.row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.row label { white-space: nowrap; }
.log-text { background: var(--card); padding: 12px; border-radius: 6px; overflow: auto; max-height: 200px; font-size: 0.85rem; }
button { margin-right: 8px; }
</style>
