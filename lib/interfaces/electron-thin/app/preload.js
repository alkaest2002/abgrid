const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  generatePDF: () => ipcRenderer.invoke("generate-pdf"),
});
