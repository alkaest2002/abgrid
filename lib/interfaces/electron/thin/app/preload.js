const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  generateReport: (data, dataType) => ipcRenderer.invoke("generate-report", data, dataType),
});
