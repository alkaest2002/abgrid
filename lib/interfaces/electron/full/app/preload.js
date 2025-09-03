const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  getElectronVersion: () => ipcRenderer.invoke("electron-version"),
  generateReport: (data, dataType) => ipcRenderer.invoke("generate-report", data, dataType),
  downloadLink: (url) => ipcRenderer.invoke("download-link", url),
});
