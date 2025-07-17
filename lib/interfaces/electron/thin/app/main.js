const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const { fork } = require("child_process");
const fs = require("fs").promises;
const os = require("os");

const ps = fork(path.resolve(__dirname, "server.js"));
let serverPort = null;

// Listen for the port from the server process
ps.on('message', (message) => {
    if (message.port) {
        serverPort = message.port;
        console.log(`Server started on port: ${serverPort}`);
        // Create window after server is ready
        if (app.isReady()) {
            createWindow();
        }
    }
});

// Handle server process errors
ps.on('error', (error) => {
    console.error('Server process error:', error);
});

ps.on('exit', (code, signal) => {
    console.log(`Server process exited with code ${code} and signal ${signal}`);
});

const createWindow = () => {
    if (!serverPort) {
        console.error('Server port not available yet');
        return;
    }
    
    const mainWindow = new BrowserWindow({
        minWidth: 980,
        minHeight: 900,
        width: 980,
        height: 900,
        webPreferences: {
            webSecurity: true,
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, "preload.js")
        }
    });

    mainWindow.loadURL(`http://127.0.0.1:${serverPort}`);
    mainWindow.webContents.openDevTools();
}

ipcMain.handle("generate-report", async (event, data, dataType) => {
    try {
        
        const win = BrowserWindow.fromWebContents(event.sender);

        let saveResult;
        let fileData;

        if (dataType === "json") {
            
            // Handle JSON data - save as JSON file
            saveResult = await dialog.showSaveDialog(win, {
                title: "Save JSON Data",
                defaultPath: path.join(os.homedir(), "Downloads", "abgrid-data.json"),
                filters: [
                    { name: "JSON Files", extensions: ["json"] },
                    { name: "All Files", extensions: ["*"] }
                ],
                properties: ["createDirectory"]
            });

            // Do nothing if user aborts
            if (saveResult.canceled)
                return;

            fileData = Buffer.from(data, "utf8");

        } else {

            // Handle HTML data - convert to PDF
            saveResult = await dialog.showSaveDialog(win, {
                title: "Save PDF",
                defaultPath: path.join(os.homedir(), "Downloads", "abgrid-report.pdf"),
                filters: [
                    { name: "PDF Files", extensions: ["pdf"] },
                    { name: "All Files", extensions: ["*"] }
                ],
                properties: ["createDirectory"]
            });

            // Do nothing if user aborts
            if (saveResult.canceled)
                return;

            // Create a temporary window to render HTML and convert to PDF
            const tempWin = new BrowserWindow({
                width: 800,
                height: 600,
                show: false,
                webPreferences: {
                    nodeIntegration: false,
                    contextIsolation: true
                }
            });

            // Load HTML content
            await tempWin.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(data)}`);

            // Wait for content to load
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Generate PDF from HTML content
            fileData = await tempWin.webContents.printToPDF({
                marginsType: 0,
                pageSize: "A4",
                printBackground: true,
                landscape: false,
                preferCSSPageSize: false
            });

            // Close temporary window
            tempWin.close();
        }

        // Save file to chosen location
        await fs.writeFile(saveResult.filePath, fileData);

        return {
            status: 200,
            message: "success"
        };

    } catch (error) {
        return {
            status: 400,
            message: "failure"
        };
    }
});

app.whenReady().then(() => {
    // Window will be created when server sends the port
    if (serverPort) {
        createWindow();
    }
});

app.on("window-all-closed", () => app.quit());
app.on("quit", () => ps.kill());
