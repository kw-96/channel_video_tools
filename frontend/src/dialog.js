/**
 * 原生文件/目录选择对话框封装（依赖 Tauri 环境）
 * 在浏览器中调用会静默失败并返回 null
 */
import { open, save } from '@tauri-apps/plugin-dialog'
import { invoke } from '@tauri-apps/api/core'

const VIDEO_FILTER = { name: '视频', extensions: ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm'] }
const IMAGE_FILTER = { name: '图片', extensions: ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'] }

/**
 * 选择多个文件
 * @param {object} [options] - { filters: [{ name, extensions }] }
 * @returns {Promise<string[]|null>} 路径数组，取消或非 Tauri 环境为 null
 */
export async function openFiles(options = {}) {
  try {
    const selected = await open({
      multiple: true,
      directory: false,
      filters: options.filters || [VIDEO_FILTER],
    })
    if (selected === null) return null
    return Array.isArray(selected) ? selected : [selected]
  } catch {
    return null
  }
}

/**
 * 选择单个文件
 * @param {object} [options] - { filters }
 * @returns {Promise<string|null>}
 */
export async function openFile(options = {}) {
  try {
    const selected = await open({
      multiple: false,
      directory: false,
      filters: options.filters || [VIDEO_FILTER],
    })
    return selected === null ? null : (Array.isArray(selected) ? selected[0] : selected)
  } catch {
    return null
  }
}

/**
 * 选择目录
 * @returns {Promise<string|null>}
 */
export async function openDir() {
  try {
    const selected = await open({
      directory: true,
      multiple: false,
    })
    return selected === null ? null : (Array.isArray(selected) ? selected[0] : selected)
  } catch {
    return null
  }
}

/**
 * 另存为对话框
 * @param {object} [options] - { defaultPath, filters }
 * @returns {Promise<string|null>}
 */
export async function saveFile(options = {}) {
  try {
    const path = await save({
      defaultPath: options.defaultPath,
      filters: options.filters || [VIDEO_FILTER],
    })
    return path ?? null
  } catch {
    return null
  }
}

/**
 * 列出目录下所有视频文件路径（仅当前目录，不递归）
 * @param {string} dir - 目录路径
 * @returns {Promise<string[]|null>} 路径数组，失败或非 Tauri 环境返回 null
 */
export async function listVideoFilesInDir(dir) {
  try {
    return await invoke('list_video_files_in_dir', { dir })
  } catch {
    return null
  }
}

export { VIDEO_FILTER, IMAGE_FILTER }
