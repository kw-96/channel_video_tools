<template>
  <div class="app" :data-theme="theme">
    <header class="titlebar" data-tauri-drag-region>
      <span class="titlebar-brand">
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
      <div class="main-inner">
        <div class="tab-settings-wrap">
          <Transition name="tab-fade" mode="out-in">
            <NormalizerTab v-if="currentTab === 'normalizer'" key="normalizer" />
            <WatermarkTab v-else-if="currentTab === 'watermark'" key="watermark" />
            <MergeTab v-else key="merge" />
          </Transition>
        </div>
        <aside class="pane-video-list" aria-label="视频列表">
          <div
            class="video-list-area"
            :class="{
              'video-list-area-empty': !videoList.length,
              'drop-zone': !videoList.length,
              'drop-zone-active': dropActive && !videoList.length,
            }"
            @dragover.prevent="dropActive = true"
            @dragleave.prevent="dropActive = false"
            @drop.prevent="onDrop"
          >
            <template v-if="!videoList.length">
              <p class="drop-zone-text">选择视频或拖拽到此处</p>
              <button type="button" class="primary drop-zone-btn" @click="openVideoDialog">选择视频文件</button>
            </template>
            <ul v-else class="video-list" role="list">
              <li
                v-for="(item, i) in videoList"
                :key="item.path + String(i)"
                class="video-list-item"
              >
                <span class="video-list-filename" :title="item.path">{{ filename(item.path) }}</span>
                <span class="video-list-status" :class="'status-' + item.status">{{ statusText(item.status) }}</span>
              </li>
            </ul>
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
    </main>
    <footer class="footer-bar">
      <div class="footer-left">
        <button type="button" class="footer-icon-btn" aria-label="设置" title="设置" @click="showSettingsDrawer = true"><Settings :size="18" /></button>
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
      </div>
      <div class="footer-actions">
        <span v-if="tabState.selectedCount > 0" class="footer-count">已选 {{ tabState.selectedCount }} 个</span>
        <button
          type="button"
          class="primary footer-start-btn"
          :disabled="!tabState.start || tabState.processing"
          @click="tabState.start?.()"
        >
          {{ tabState.processing ? '处理中...' : '开始处理' }}
        </button>
        <button
          type="button"
          class="secondary footer-reset-btn"
          :disabled="!tabState.reset || tabState.processing"
          @click="tabState.reset?.()"
        >
          重置
         </button>
      </div>
    </footer>
    </div>
    <Teleport to="body">
      <Transition name="drawer">
        <div v-if="showSettingsDrawer" class="settings-drawer-backdrop" aria-hidden="true" @click="showSettingsDrawer = false" />
      </Transition>
      <Transition name="drawer">
        <aside
          v-if="showSettingsDrawer"
          class="settings-drawer-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="settings-drawer-title"
          @click.stop
        >
          <header class="settings-drawer-header">
            <h2 id="settings-drawer-title" class="settings-drawer-title">设置</h2>
            <button type="button" class="settings-drawer-close" aria-label="关闭" @click="showSettingsDrawer = false">×</button>
          </header>
          <div class="settings-drawer-body">
            <div class="settings-drawer-row">
              <span class="settings-drawer-label">外观</span>
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
              <span class="settings-drawer-value">{{ theme === 'dark' ? '深色' : '浅色' }}</span>
            </div>
          </div>
        </aside>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, provide, watch } from 'vue'
import { Sun, Moon, Settings, ScanLine, ImagePlus, Merge } from 'lucide-vue-next'
import { getCurrentWindow } from '@tauri-apps/api/window'
import { getTheme, setTheme } from './api'
import { useVideoImport } from './composables/useVideoImport'
import NormalizerTab from './views/NormalizerTab.vue'
import WatermarkTab from './views/WatermarkTab.vue'
import MergeTab from './views/MergeTab.vue'
import VideoImportDialog from './components/VideoImportDialog.vue'

const VIDEO_EXT = new Set(['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'])

function isVideoPath(p) {
  const lower = p.toLowerCase()
  return [...VIDEO_EXT].some(ext => lower.endsWith(ext))
}

let unlistenDrop = null
let unregAppDrop = null
onMounted(async () => {
  unregAppDrop = registerAppDrop()
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
  if (unregAppDrop) unregAppDrop()
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
const showSettingsDrawer = ref(false)

const tabState = reactive({ start: null, processing: false, reset: null, selectedCount: 0 })
provide('tabState', tabState)

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
} = useVideoImport({ onLog: () => {} })

const videoImport = {
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
}
provide('videoImport', videoImport)

watch(() => videoList.value.length, (n) => { tabState.selectedCount = n }, { immediate: true })

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
  height: 40px;
  padding: 0 0 0 16px;
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
  height: 40px;
  min-height: 40px;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--fg-muted);
  font-size: 22px;
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
  display: grid;
  grid-template-columns: 140px minmax(240px, 320px) 1fr;
  grid-template-rows: 1fr auto;
}

.sidebar {
  grid-column: 1;
  grid-row: 1 / -1;
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
  padding: 10px 8px;
  margin: 0;
  border: none;
  border-left: 3px solid transparent;
  border-radius: 0;
  background: transparent;
  color: var(--fg-muted);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
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
  flex: 0 1 auto;
  white-space: nowrap;
}

.content {
  grid-column: 2 / 4;
  grid-row: 1;
  min-width: 0;
  min-height: 0;
  padding: 0;
  background: var(--bg);
  overflow: auto;
  overflow-x: hidden;
}

.content-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.main-inner {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: row;
}

.tab-settings-wrap {
  flex: 1 1 320px;
  min-width: 240px;
  max-width: 320px;
  padding: 16px 0 16px 16px;
  overflow: auto;
  font-size: 13px;
}
.tab-settings-wrap .section-title {
  font-size: 0.8125rem;
}
.tab-settings-wrap .form-row label {
  font-size: 13px;
}
.tab-settings-wrap .hint {
  font-size: 12px;
}
.tab-settings-wrap button,
.tab-settings-wrap .segmented button {
  font-size: 12px;
}
.tab-settings-wrap input,
.tab-settings-wrap select {
  font-size: 12px;
}

.pane-video-list {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.video-list-area {
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: auto;
  border: none;
  border-radius: 0;
}
.video-list-area.video-list-area-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  margin-top: 0;
}
.video-list-area.video-list-area-empty.drop-zone {
  border: none;
  border-radius: 0;
}
.video-list-area:not(.video-list-area-empty) {
  border: none;
  border-radius: 0;
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

.footer-bar {
  grid-column: 1 / -1;
  grid-row: 2;
  flex-shrink: 0;
  height: var(--footer-height);
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-elevated);
  border-top: 1px solid var(--border);
  position: relative;
  z-index: 10000;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
}

[data-theme="dark"] .footer-bar {
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.12);
}
.footer-left {
  display: flex;
  align-items: center;
  gap: 4px;
}
.footer-icon-btn {
  width: 28px;
  height: 28px;
  min-height: 28px;
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
.footer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.footer-count {
  font-size: 13px;
  color: var(--fg-muted);
}
.footer-start-btn {
  min-width: 88px;
}
.footer-reset-btn {
  min-width: 56px;
}

.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.15s ease;
}

.tab-fade-enter-from,
.tab-fade-leave-to {
  opacity: 0;
}

/* 设置抽屉：从状态栏往上拉出，占半屏 */
.settings-drawer-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: var(--footer-height);
  background: rgba(0, 0, 0, 0.35);
  z-index: 9998;
}

.settings-drawer-panel {
  position: fixed;
  bottom: var(--footer-height);
  left: 0;
  right: 0;
  height: 50vh;
  min-height: 280px;
  transform-origin: bottom;
  background: var(--bg-elevated);
  border-top-left-radius: var(--radius-lg);
  border-top-right-radius: var(--radius-lg);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.08), 0 -16px 48px rgba(0, 0, 0, 0.12);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

[data-theme="dark"] .settings-drawer-panel {
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.2), 0 -16px 48px rgba(0, 0, 0, 0.35);
}

.settings-drawer-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}

.settings-drawer-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--fg);
}

.settings-drawer-close {
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: var(--fg-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition-fast), background-color var(--transition-fast);
}

.settings-drawer-close:hover {
  color: var(--fg);
  background: var(--card-hover);
}

.settings-drawer-body {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.settings-drawer-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
}

.settings-drawer-label {
  font-size: 13px;
  color: var(--fg);
}

.settings-drawer-value {
  font-size: 13px;
  color: var(--fg-muted);
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}

.drawer-enter-active.settings-drawer-panel,
.drawer-leave-active.settings-drawer-panel {
  transition: transform 0.25s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from.settings-drawer-panel,
.drawer-leave-to.settings-drawer-panel {
  transform: scaleY(0);
}
</style>
