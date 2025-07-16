const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { fork } = require('child_process');
const fs = require('fs').promises;
const os = require('os');

const ps = fork(path.resolve(__dirname, "server.js"));
const port = "53472";

const createWindow = () => {
  const mainWindow = new BrowserWindow({
    minWidth: 980,
    minHeight: 900,
    width: 980,
    height: 900,
    webPreferences: { 
      webSecurity: true,
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });
  
  mainWindow.loadURL(`http://127.0.0.1:${port}`);
  mainWindow.webContents.openDevTools();
}

// PDF Generation with Save Dialog
ipcMain.handle('generate-pdf', async (event) => {
  try {
    const win = BrowserWindow.fromWebContents(event.sender);
    
    // Show save dialog
    const saveResult = await dialog.showSaveDialog(win, {
      title: 'Save PDF',
      defaultPath: path.join(os.homedir(), 'Downloads', 'document.pdf'),
      filters: [
        { name: 'PDF Files', extensions: ['pdf'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['createDirectory']
    });

    // If user cancelled the dialog
    if (saveResult.canceled) {
      return { success: false, cancelled: true };
    }

    // Generate PDF from web content
    const pdfData = await win.webContents.printToPDF({
      marginsType: 0,
      pageSize: 'A4',
      printBackground: true,
      landscape: false,
      preferCSSPageSize: false
    });

    // Save PDF to chosen location
    await fs.writeFile(saveResult.filePath, pdfData);

    return { 
      success: true, 
      filePath: saveResult.filePath,
      message: 'PDF saved successfully!'
    };

  } catch (error) {
    console.error('PDF generation failed:', error);
    return { 
      success: false, 
      error: error.message 
    };
  }
});

// PDF Generation with Auto-Open
ipcMain.handle('generate-and-open-pdf', async (event) => {
  try {
    const win = BrowserWindow.fromWebContents(event.sender);
    const tempPath = path.join(os.tmpdir(), `pdf-${Date.now()}.pdf`);
    
    // Generate PDF
    const pdfData = await win.webContents.printToPDF({
      marginsType: 0,
      pageSize: 'A4',
      printBackground: true,
      landscape: false
    });

    // Save to temp location
    await fs.writeFile(tempPath, pdfData);
    
    // Open with default application
    const { shell } = require('electron');
    await shell.openExternal(`file://${tempPath}`);

    return { 
      success: true, 
      filePath: tempPath,
      message: 'PDF generated and opened!'
    };

  } catch (error) {
    console.error('PDF generation failed:', error);
    return { 
      success: false, 
      error: error.message 
    };
  }
});

app.whenReady().then(() => createWindow());
app.on('window-all-closed', () => app.quit());
app.on('quit', () => ps.kill());
