const {app, BrowserWindow} = require('electron');
const path = require('path');
const { fork } = require('child_process');

const ps = fork(path.resolve(__dirname, "server.js"));
const port = "53472";
const createWindow = () => {

  const mainWindow = new BrowserWindow({
    minWidth: 980,
    minHeight: 900,
    width: 980,
    height: 900,
    webPreferences: { webSecurity: true }
  });
  
  mainWindow.loadURL(`http://127.0.0.1:${port}`);
  mainWindow.webContents.openDevTools()
}

app.whenReady().then(() => createWindow());
app.on('window-all-closed', () => app.quit());
app.on('quit', () => ps.kill());