/**
 * 批量视频导入逻辑（拖拽、弹窗、文件/文件夹选择）
 * 供视频填充、视频水印等 Tab 复用，保证选择视频的实现统一
 */
import { ref, computed } from 'vue'
import { openFiles, openDir, listVideoFilesInDir } from '../dialog'

const STATUS_MAP = { pending: '待处理', processing: '处理中', success: '成功', fail: '失败' }

/**
 * @param {{ onLog?: (msg: string) => void, maxItems?: number }} [options]
 *   maxItems: 列表最大条数，如 1 表示仅保留首个（合并 Tab 主体视频等）
 * @returns 视频列表状态、弹窗状态、拖拽区状态、操作方法及展示用工具函数
 */
export function useVideoImport(options = {}) {
  const onLog = options.onLog || (() => {})
  const maxItems = options.maxItems

  const videoList = ref([])
  const videoDialogOpen = ref(false)
  const dropActive = ref(false)

  const inputPaths = computed(() => videoList.value.map(i => i.path))

  function openVideoDialog() {
    videoDialogOpen.value = true
  }

  function closeVideoDialog() {
    videoDialogOpen.value = false
  }

  function appendPaths(newPaths) {
    if (maxItems === 1) {
      if (newPaths.length) {
        videoList.value = [{ path: newPaths[0], status: 'pending' }]
        onLog(`已选择主体视频`)
      }
      return
    }
    const set = new Set(videoList.value.map(i => i.path))
    for (const p of newPaths) {
      if (!set.has(p)) {
        set.add(p)
        videoList.value.push({ path: p, status: 'pending' })
      }
    }
    if (newPaths.length) {
      onLog(`已添加 ${newPaths.length} 个文件，当前共 ${videoList.value.length} 个`)
    }
  }

  async function pickInputFiles() {
    const paths = await openFiles()
    if (paths?.length) appendPaths(paths)
  }

  async function pickInputFolder() {
    const dir = await openDir()
    if (!dir) return
    const paths = await listVideoFilesInDir(dir)
    if (paths?.length) {
      appendPaths(paths)
      onLog(`已添加文件夹内 ${paths.length} 个视频，当前共 ${videoList.value.length} 个`)
    } else {
      onLog('该文件夹内没有视频文件')
    }
  }

  async function handleAddFiles() {
    closeVideoDialog()
    await pickInputFiles()
  }

  async function handleAddFolder() {
    closeVideoDialog()
    await pickInputFolder()
  }

  function onDrop(e) {
    dropActive.value = false
    e.preventDefault()
  }

  function filename(path) {
    const idx = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'))
    return idx >= 0 ? path.slice(idx + 1) : path
  }

  function statusText(s) {
    return STATUS_MAP[s] || s
  }

  /** 注册全局拖放监听，返回取消注册函数 */
  function registerAppDrop() {
    const handler = (e) => {
      const paths = e.detail?.paths
      if (paths?.length) appendPaths(maxItems === 1 ? paths.slice(0, 1) : paths)
    }
    window.addEventListener('app-file-drop', handler)
    return () => window.removeEventListener('app-file-drop', handler)
  }

  function clearVideoList() {
    videoList.value = []
  }

  return {
    videoList,
    inputPaths,
    videoDialogOpen,
    openVideoDialog,
    closeVideoDialog,
    dropActive,
    onDrop,
    appendPaths,
    handleAddFiles,
    handleAddFolder,
    filename,
    statusText,
    STATUS_MAP,
    registerAppDrop,
    clearVideoList,
  }
}
