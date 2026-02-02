<template>
  <div class="tab-settings">
    <section class="section-card" aria-label="功能设置">
      <h3 class="section-title">输出目录</h3>
      <div class="btn-text-row">
        <button type="button" class="secondary" @click="pickOutputDir">浏览</button>
        <span class="selection-display">{{ outputDir || '请选择输出目录' }}</span>
      </div>
      <h3 class="section-title pos-title">插入位置</h3>
      <div class="segmented" role="group" aria-label="插入位置">
        <button type="button" :class="{ active: insertPosition === 'head' }" @click="insertPosition = 'head'">片头</button>
        <button type="button" :class="{ active: insertPosition === 'tail' }" @click="insertPosition = 'tail'">片尾</button>
      </div>
      <h3 class="section-title pos-title">插入视频</h3>
      <div class="btn-text-row">
        <button type="button" class="secondary" @click="pickInsertVideo">选择视频</button>
        <span class="selection-display">{{ displayPath(insertVideo) || '请选择要插入的视频文件' }}</span>
      </div>
    </section>
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
import { ref, inject, onMounted, onUnmounted, watch } from 'vue'
import { merge } from '../api'
import { openFile, openDir } from '../dialog'

const tabState = inject('tabState')
const { videoList, inputPaths, filename, statusText, clearVideoList } = inject('videoImport')

const logLines = ref([])
function log(msg) {
  const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logLines.value.push(`[${ts}] ${msg}`)
}

const insertVideo = ref('')

function displayPath(p) {
  if (!p) return ''
  const idx = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'))
  return idx >= 0 ? p.slice(idx + 1) : p
}

const outputDir = ref('')
const insertPosition = ref('head')
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

async function pickInsertVideo() {
  const path = await openFile()
  if (path) insertVideo.value = path
}

async function pickOutputDir() {
  const dir = await openDir()
  if (dir) outputDir.value = dir
}

function closeDoneModal() {
  doneModalOpen.value = false
}

function joinPath(dir, name) {
  if (dir.endsWith('/') || dir.endsWith('\\')) return dir + name
  return dir + (dir.includes('/') ? '/' : '\\') + name
}

async function start() {
  const paths = inputPaths.value
  if (!paths.length) {
    log('请先选择主体视频')
    return
  }
  if (!insertVideo.value) {
    log('请选择插入视频')
    return
  }
  if (!outputDir.value) {
    log('请选择输出目录')
    return
  }
  processing.value = true
  progress.value = 0
  videoList.value.forEach(i => { i.status = 'processing' })
  log('开始批量合并...')
  let okCount = 0
  let failCount = 0
  const total = paths.length
  for (let i = 0; i < paths.length; i++) {
    const mainVideo = paths[i]
    const outName = filename(mainVideo)
    const outputPath = joinPath(outputDir.value, outName)
    try {
      const res = await merge({
        main_video: mainVideo,
        insert_video: insertVideo.value,
        output_path: outputPath,
        insert_position: insertPosition.value,
      })
      const item = videoList.value.find((x) => x.path === mainVideo)
      if (item) item.status = res.ok ? 'success' : 'fail'
      if (res.ok) {
        okCount++
        log(`${outName} 合并完成`)
      } else {
        failCount++
        log(`${outName} 合并失败: ${res.message || ''}`)
      }
    } catch (e) {
      const item = videoList.value.find((x) => x.path === mainVideo)
      if (item) item.status = 'fail'
      failCount++
      log(`${filename(mainVideo)} 请求失败: ${e.message}`)
    }
    progress.value = Math.round(((i + 1) / total) * 100)
  }
  processing.value = false
  doneModalMsg.value = `成功 ${okCount} 个，失败 ${failCount} 个`
  doneModalOpen.value = true
}

function reset() {
  clearVideoList()
  insertVideo.value = ''
  outputDir.value = ''
  insertPosition.value = 'head'
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
</style>
