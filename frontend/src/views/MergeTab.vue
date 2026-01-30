<template>
  <div class="panel">
    <section class="section">
      <h2 class="section-title">主体视频</h2>
      <input v-model="mainVideo" type="text" placeholder="主体视频路径" class="full-width" />
    </section>
    <section class="section">
      <h2 class="section-title">插入视频（片头/片尾）</h2>
      <input v-model="insertVideo" type="text" placeholder="插入视频路径" class="full-width" />
    </section>
    <section class="section">
      <h2 class="section-title">输出路径</h2>
      <input v-model="outputPath" type="text" placeholder="合并后输出文件路径" class="full-width" />
    </section>
    <section class="section">
      <h2 class="section-title">插入位置</h2>
      <select v-model="insertPosition">
        <option value="head">片头</option>
        <option value="tail">片尾</option>
      </select>
    </section>
    <section class="section">
      <button class="primary" :disabled="processing" @click="start">开始合并</button>
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
import { merge } from '../api'

const mainVideo = ref('')
const insertVideo = ref('')
const outputPath = ref('')
const insertPosition = ref('head')
const processing = ref(false)
const logLines = ref([])

const logText = computed(() => logLines.value.join('\n') || '[暂无日志]')

function log(msg) {
  const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logLines.value.push(`[${ts}] ${msg}`)
}

async function start() {
  if (!mainVideo.value.trim()) {
    log('请填写主体视频路径')
    return
  }
  if (!insertVideo.value.trim()) {
    log('请填写插入视频路径')
    return
  }
  if (!outputPath.value.trim()) {
    log('请填写输出路径')
    return
  }
  processing.value = true
  log('开始合并...')
  try {
    const res = await merge({
      main_video: mainVideo.value.trim(),
      insert_video: insertVideo.value.trim(),
      output_path: outputPath.value.trim(),
      insert_position: insertPosition.value,
    })
    if (res.ok) log('合并完成')
    else log(res.message || '合并失败')
  } catch (e) {
    log('请求失败: ' + e.message)
  }
  processing.value = false
}

function reset() {
  mainVideo.value = ''
  insertVideo.value = ''
  outputPath.value = ''
  insertPosition.value = 'head'
  logLines.value = []
}
</script>

<style scoped>
.panel { max-width: 800px; }
.section { margin-bottom: 16px; }
.section-title { margin: 0 0 8px; font-size: 0.95rem; }
.full-width { width: 100%; }
.log-text { background: var(--card); padding: 12px; border-radius: 6px; overflow: auto; max-height: 200px; font-size: 0.85rem; }
button { margin-right: 8px; }
</style>
