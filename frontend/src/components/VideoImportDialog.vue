<template>
  <div
    v-if="show"
    class="dialog-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="video-import-dialog-title"
    @click.self="$emit('close')"
  >
    <div class="dialog-box">
      <button type="button" class="dialog-close" aria-label="关闭" @click="$emit('close')">
        <X :size="18" />
      </button>
      <div class="dialog-header">
        <h2 id="video-import-dialog-title" class="dialog-title">选择视频</h2>
      </div>
      <div class="dialog-actions">
        <button type="button" class="primary" @click="$emit('add-files')">添加文件</button>
        <button type="button" class="primary" @click="$emit('add-folder')">添加文件夹</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { X } from 'lucide-vue-next'

defineProps({
  show: { type: Boolean, default: false },
})
defineEmits(['close', 'add-files', 'add-folder'])
</script>
