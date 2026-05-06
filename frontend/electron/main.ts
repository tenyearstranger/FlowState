import { app, BrowserWindow, dialog, ipcMain, shell, type OpenDialogOptions } from 'electron'
import path from 'node:path'

const isDev = !app.isPackaged
const devServerUrl = process.env.ELECTRON_RENDERER_URL ?? 'http://127.0.0.1:5174'

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  if (isDev) {
    win.loadURL(devServerUrl)
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

app.whenReady().then(() => {
  ipcMain.handle('dialog:choose-directory', async () => {
    const browserWindow = BrowserWindow.getFocusedWindow()
    const options: OpenDialogOptions = { properties: ['openDirectory'] }
    const result = browserWindow
      ? await dialog.showOpenDialog(browserWindow, options)
      : await dialog.showOpenDialog(options)

    if (result.canceled || result.filePaths.length === 0) {
      return null
    }

    return result.filePaths[0]
  })

  ipcMain.handle('shell:open-path', async (_, targetPath: string) => {
    if (!targetPath) {
      return 'Path is required'
    }
    return shell.openPath(targetPath)
  })

  ipcMain.handle('shell:show-item-in-folder', async (_, targetPath: string) => {
    if (!targetPath) {
      return false
    }
    shell.showItemInFolder(targetPath)
    return true
  })

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
