<template>
  <div class="app" :data-theme="theme">
    <header class="titlebar" data-tauri-drag-region>
      <span class="titlebar-brand">
        <Play class="titlebar-icon" :size="16" fill="currentColor" />
        <span class="titlebar-title">视频批量处理</span>
      </span>
      <div class="titlebar-controls">
        <button type="button" class="titlebar-btn" aria-label="最小化" @click="onMinimize">-</button>
        <button type="button" class="titlebar-btn" aria-label="最大化" @click="onMaximize">□</button>
        <button type="button" class="titlebar-btn titlebar-close" aria-label="关闭" @click="onClose">×</button>
      </div>
    </header>
    <div class="content-wrap">
    <aside class="sidebar" role="navigation" aria-label="功能导航">
      <nav class="nav-list" role="tablist">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          role="tab"
          :aria-selected="currentTab === tab.id"
          :class="['nav-item', { active: currentTab === tab.id }]"
          @click="currentTab = tab.id"
        >
          <component :is="tab.icon" class="nav-icon" :size="18" />
          <span class="nav-label">{{ tab.label }}</span>
        </button>
      </nav>
    </aside>
    <main class="content content-body" role="main" aria-label="功能设置与视频列表">
      <Transition name="tab-fade" mode="out-in">
        <NormalizerTab v-if="currentTab === 'normalizer'" key="normalizer" />
        <WatermarkTab v-else-if="currentTab === 'watermark'" key="watermark" />
        <MergeTab v-else key="merge" />
      </Transition>
    </main>
    </div>
    <footer class="footer-bar">
      <div class="footer-left">
        <button type="button" class="footer-icon-btn" aria-label="设置" title="设置"><Settings :size="18" /></button>
        <button
          type="button"
          class="footer-icon-btn"
          :title="theme === 'dark' ? '切换到浅色' : '切换到深色'"
          :aria-label="theme === 'dark' ? '切换到浅色' : '切换到深色'"
          @click="toggleTheme"
        >
          <Sun v-if="theme === 'dark'" :size="18" aria-hidden="true" />
          <Moon v-else :size="18" aria-hidden="true" />
        </button>
        <button type="button" class="footer-icon-btn" aria-label="菜单" title="菜单"><Menu :size="18" /></button>
      </div>
      <button
        type="button"
        class="primary footer-start-btn"
        :disabled="!tabState.start || tabState.processing"
        @click="tabState.start?.()"
      >
        {{ tabState.processing ? '处理中...' : '开始处理' }}
      </button>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, provide } from 'vue'
import { Sun, Moon, Play, Settings, Menu, ScanLine, ImagePlus, Merge } from 'lucide-vue-next'
import { getCurrentWindow } from '@tauri-apps/api/window'
import { getTheme, setTheme } from './api'
import NormalizerTab from './views/NormalizerTab.vue'
import WatermarkTab from './views/WatermarkTab.vue'
import MergeTab from './views/MergeTab.vue'

const VIDEO_EXT = new Set(['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'])

function isVideoPath(p) {
  const lower = p.toLowerCase()
  return [...VIDEO_EXT].some(ext => lower.endsWith(ext))
}

let unlistenDrop = null
onMounted(async () => {
  try {
    const w = getCurrentWindow()
    unlistenDrop = await w.onDragDropEvent((ev) => {
      if (ev.payload?.type === 'drop' && ev.payload?.paths?.length) {
        const paths = ev.payload.paths.filter(isVideoPath)
        if (paths.length) {
          window.dispatchEvent(new CustomEvent('app-file-drop', { detail: { paths } }))
        }
      }
    })
  } catch (_) {}
})
onUnmounted(() => {
  if (unlistenDrop) unlistenDrop()
})

function onMinimize() {
  getCurrentWindow().minimize()
}
function onMaximize() {
  getCurrentWindow().toggleMaximize()
}
function onClose() {
  getCurrentWindow().close()
}

const tabs = [
  { id: 'normalizer', label: '视频填充', icon: ScanLine },
  { id: 'watermark', label: '视频水印', icon: ImagePlus },
  { id: 'merge', label: '视频合并', icon: Merge },
]
const currentTab = ref('normalizer')
const theme = ref('dark')

const tabState = reactive({ start: null, processing: false })
provide('tabState', tabState)

async function loadTheme() {
  try {
    theme.value = await getTheme()
  } catch {
    theme.value = 'dark'
  }
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  setTheme(theme.value).catch(() => {})
}

onMounted(loadTheme)
</script>

<style scoped>
.app {
  height: 100vh;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.titlebar {
  flex-shrink: 0;
  height: 36px;
  padding: 0 12px 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  user-select: none;
}

.titlebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.titlebar-icon {
  flex-shrink: 0;
  color: var(--primary);
}
.titlebar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fg);
}

.titlebar-controls {
  display: flex;
  align-items: center;
  gap: 0;
}

.titlebar-btn {
  width: 40px;
  height: 36px;
  min-height: 36px;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--fg-muted);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.titlebar-btn:hover {
  background: var(--card-hover);
  color: var(--fg);
}

.titlebar-btn.titlebar-close:hover {
  background: #c42b1c;
  color: #fff;
}

.content-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: row;
}

.sidebar {
  width: 140px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-elevated);
  border-right: 1px solid var(--border);
}

.nav-list {
  flex: 1;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  width: 100%;
  padding: 10px 12px 10px 14px;
  margin: 0;
  border: none;
  border-left: 3px solid transparent;
  border-radius: 0;
  background: transparent;
  color: var(--fg-muted);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: left;
  transition: color var(--transition-fast), background-color var(--transition-fast), border-color var(--transition-fast);
}

.nav-item:hover {
  color: var(--fg);
  background: var(--card-hover);
}

.nav-item.active {
  color: var(--primary);
  background: var(--card-hover);
  border-left-color: var(--primary);
}

.nav-item.active .nav-icon {
  color: var(--primary);
}

.nav-item:focus-visible {
  outline: none;
  color: var(--fg);
  background: var(--card-hover);
}

.nav-item.active:focus-visible {
  color: var(--primary);
  background: var(--card-hover);
  border-left-color: var(--primary);
}

.nav-icon {
  flex-shrink: 0;
  opacity: 0.9;
  color: inherit;
}

.nav-label {
  flex: 1;
  white-space: nowrap;
}

.content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 0;
  background: var(--bg);
  overflow: auto;
}

.content-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.footer-bar {
  flex-shrink: 0;
  height: 48px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-elevated);
  border-top: 1px solid var(--border);
}
.footer-left {
  display: flex;
  align-items: center;
  gap: 4px;
}
.footer-icon-btn {
  width: 36px;
  height: 36px;
  min-height: 36px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--fg-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}
.footer-icon-btn:hover {
  background: var(--card-hover);
  color: var(--fg);
}
.footer-start-btn {
  min-width: 120px;
}

.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.15s ease;
}

.tab-fade-enter-from,
.tab-fade-leave-to {
  opacity: 0;
}
</style>
