<template>
  <div class="panel">
    <section class="section">
      <h2 class="section-title">输入视频</h2>
      <textarea v-model="inputPathsText" rows="2" placeholder="视频路径，每行一个"></textarea>
    </section>
    <section class="section">
      <h2 class="section-title">水印图片</h2>
      <input v-model="watermarkPath" type="text" placeholder="水印图片路径" class="full-width" />
    </section>
    <section class="section">
      <h2 class="section-title">输出目录</h2>
      <input v-model="outputDir" type="text" placeholder="输出目录路径" class="full-width" />
    </section>
    <section class="section">
      <h2 class="section-title">参数</h2>
      <div class="row">
        <label>不透明度</label>
        <input v-model.number="opacity" type="number" min="0" max="1" step="0.1" style="width:80px" />
        <label>位置</label>
        <select v-model="position">
          <option value="top_left">左上</option>
          <option value="top">上中</option>
          <option value="top_right">右上</option>
          <option value="left">左中</option>
          <option value="center">居中</option>
          <option value="right">右中</option>
          <option value="bottom_left">左下</option>
          <option value="bottom">下中</option>
          <option value="bottom_right">右下</option>
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
import { watermark } from '../api'

const inputPathsText = ref('')
const watermarkPath = ref('')
const outputDir = ref('')
const opacity = ref(1.0)
const position = ref('center')
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

async function start() {
  const paths = inputPaths.value
  if (!paths.length) {
    log('请先输入视频路径')
    return
  }
  if (!watermarkPath.value.trim()) {
    log('请填写水印图片路径')
    return
  }
  if (!outputDir.value.trim()) {
    log('请填写输出目录')
    return
  }
  processing.value = true
  log('开始添加水印...')
  try {
    const res = await watermark({
      input_paths: paths,
      output_dir: outputDir.value.trim(),
      watermark_path: watermarkPath.value.trim(),
      opacity: opacity.value,
      position: position.value,
    })
    if (res.ok) log('全部处理完成')
    else {
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
  watermarkPath.value = ''
  outputDir.value = ''
  opacity.value = 1.0
  position.value = 'center'
  logLines.value = []
}
</script>

<style scoped>
.panel { max-width: 800px; }
.section { margin-bottom: 16px; }
.section-title { margin: 0 0 8px; font-size: 0.95rem; }
.full-width { width: 100%; }
.row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.row label { white-space: nowrap; }
.log-text { background: var(--card); padding: 12px; border-radius: 6px; overflow: auto; max-height: 200px; font-size: 0.85rem; }
button { margin-right: 8px; }
</style>
