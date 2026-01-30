<template>
  <div class="app" :data-theme="theme">
    <header class="header">
      <h1 class="title">渠道视频批量处理工具</h1>
      <button class="theme-btn" :title="theme === 'dark' ? '切换到浅色' : '切换到深色'" @click="toggleTheme">
        {{ theme === 'dark' ? '浅色' : '深色' }}
      </button>
    </header>
    <nav class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab', { active: currentTab === tab.id }]"
        @click="currentTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </nav>
    <main class="content">
      <NormalizerTab v-show="currentTab === 'normalizer'" />
      <WatermarkTab v-show="currentTab === 'watermark'" />
      <MergeTab v-show="currentTab === 'merge'" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTheme, setTheme } from './api'
import NormalizerTab from './views/NormalizerTab.vue'
import WatermarkTab from './views/WatermarkTab.vue'
import MergeTab from './views/MergeTab.vue'

const tabs = [
  { id: 'normalizer', label: '视频规范' },
  { id: 'watermark', label: '视频水印' },
  { id: 'merge', label: '视频合并' },
]
const currentTab = ref('normalizer')
const theme = ref('dark')

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
.app { min-height: 100vh; }
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
}
.title { margin: 0; font-size: 1.1rem; }
.theme-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--fg);
  cursor: pointer;
}
.theme-btn:hover { opacity: 0.9; }
.tabs {
  display: flex;
  gap: 4px;
  padding: 8px 12px 0;
  border-bottom: 1px solid var(--border);
}
.tab {
  padding: 8px 16px;
  border: none;
  border-radius: 6px 6px 0 0;
  background: transparent;
  color: var(--fg);
  cursor: pointer;
}
.tab.active {
  background: var(--card);
  font-weight: 600;
}
.content { padding: 16px; }
</style>
