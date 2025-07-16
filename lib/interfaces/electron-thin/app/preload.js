const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  generatePDF: () => ipcRenderer.invoke("generate-pdf"),
  generateAndOpenPDF: () => ipcRenderer.invoke("generate-and-open-pdf")
});
