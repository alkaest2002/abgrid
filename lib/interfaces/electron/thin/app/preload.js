const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  generateReport: (data, dataType) => ipcRenderer.invoke("generate-report", data, dataType),
  downloadManual: (url) => ipcRenderer.send("download-manual", url),
});
