/**
 * 单文件视频选择弹窗逻辑（与批量导入使用同一弹窗 UI）
 * 供合并 Tab 等“选一个视频”场景复用，实现统一
 */
import { ref } from 'vue'
import { openFiles, openDir, listVideoFilesInDir } from '../dialog'

/**
 * @param {(context: string, path: string) => void} onSelected - 选择完成后回调 (context, 第一个路径)
 * @returns 弹窗状态与操作方法
 */
export function useSingleVideoDialog(onSelected) {
  const videoDialogOpen = ref(false)
  const dialogContext = ref(null)

  function openVideoDialog(context) {
    dialogContext.value = context
    videoDialogOpen.value = true
  }

  function closeVideoDialog() {
    videoDialogOpen.value = false
    dialogContext.value = null
  }

  async function handleAddFiles() {
    const ctx = dialogContext.value
    closeVideoDialog()
    const paths = await openFiles()
    if (paths?.length && ctx) onSelected(ctx, paths[0])
  }

  async function handleAddFolder() {
    const ctx = dialogContext.value
    closeVideoDialog()
    const dir = await openDir()
    if (!dir) return
    const paths = await listVideoFilesInDir(dir)
    if (paths?.length && ctx) onSelected(ctx, paths[0])
  }

  return {
    videoDialogOpen,
    openVideoDialog,
    closeVideoDialog,
    handleAddFiles,
    handleAddFolder,
  }
}
