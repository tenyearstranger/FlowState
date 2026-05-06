import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  ping: () => 'pong',
  chooseDirectory: () => ipcRenderer.invoke('dialog:choose-directory') as Promise<string | null>,
  openPath: (targetPath: string) =>
    ipcRenderer.invoke('shell:open-path', targetPath) as Promise<string>,
  showItemInFolder: (targetPath: string) =>
    ipcRenderer.invoke('shell:show-item-in-folder', targetPath) as Promise<boolean>,
})
