const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const { fork } = require("child_process");
const fs = require("fs").promises;
const os = require("os");

class ElectronApp {
    constructor() {
        this.serverProcess = null;
        this.serverPort = null;
        this.mainWindow = null;
        this.isQuitting = false;
    }

    /**
     * Initialize and start the server process
     */
    initializeServer() {
        const serverPath = path.resolve(__dirname, "server.js");
        this.serverProcess = fork(serverPath);

        // Listen for server messages
        this.serverProcess.on('message', (message) => {
            if (message.port) {
                this.serverPort = message.port;
                console.log(`Server started on port: ${this.serverPort}`);
                
                // Create window if app is ready
                if (app.isReady() && !this.mainWindow) {
                    this.createWindow();
                }
            }
        });

        // Handle server errors
        this.serverProcess.on('error', (error) => {
            console.error('Server process error:', error);
            if (!this.isQuitting) {
                this.showErrorDialog('Server Error', `Failed to start server: ${error.message}`);
            }
        });

        this.serverProcess.on('exit', (code, signal) => {
            console.log(`Server process exited with code ${code} and signal ${signal}`);
            if (!this.isQuitting && code !== 0) {
                this.showErrorDialog('Server Crashed', 'The local server has stopped unexpectedly.');
            }
        });
    }

    /**
     * Show error dialog to user
     */
    showErrorDialog(title, message) {
        if (this.mainWindow && !this.mainWindow.isDestroyed()) {
            dialog.showErrorBox(title, message);
        }
    }

    /**
     * Create the main application window
     */
    createWindow() {
        if (!this.serverPort) {
            console.error('Cannot create window: Server port not available');
            return;
        }

        if (this.mainWindow && !this.mainWindow.isDestroyed()) {
            this.mainWindow.focus();
            return;
        }

        this.mainWindow = new BrowserWindow({
            minWidth: 900,
            minHeight: 870,
            width: 900,
            height: 870,
            webPreferences: {
                webSecurity: true,
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, "preload.js")
            }
        });

        this.mainWindow.loadURL(`http://127.0.0.1:${this.serverPort}`);
        
        // Handle window closed
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        // Prevent user from resizing window
        this.mainWindow.on('will-resize', (event) => {
            event.preventDefault()
        });
        
        // Uncomment for development
        // this.mainWindow.webContents.openDevTools();
    }

    /**
     * Validate report generation parameters
     */
    validateReportParams(data, dataType) {
        if (!data || typeof data !== 'string') {
            throw new Error('invalid_data');
        }

        if (!['json', 'html', 'pdf'].includes(dataType)) {
            throw new Error('invalid_data_type');
        }

        if (data.length === 0) {
            throw new Error('empty_data_provided');
        }
    }

    /**
     * Generate JSON report
     */
    async generateJsonReport(data, parentWindow) {
        const saveResult = await dialog.showSaveDialog(parentWindow, {
            title: "Save JSON Data",
            defaultPath: path.join(os.homedir(), "Downloads", "abgrid-data.json"),
            filters: [
                { name: "JSON Files", extensions: ["json"] },
                { name: "All Files", extensions: ["*"] }
            ],
            properties: ["createDirectory"]
        });

        if (saveResult.canceled) {
            return;
        }

        const fileData = Buffer.from(data, "utf8");
        await fs.writeFile(saveResult.filePath, fileData);
        
        return { status: 200, message: "success" };
    }

    /**
     * Generate PDF report
     */
    async generatePdfReport(data, parentWindow) {
        const saveResult = await dialog.showSaveDialog(parentWindow, {
            title: "Save PDF Report",
            defaultPath: path.join(os.homedir(), "Downloads", "abgrid-report.pdf"),
            filters: [
                { name: "PDF Files", extensions: ["pdf"] },
                { name: "All Files", extensions: ["*"] }
            ],
            properties: ["createDirectory"]
        });

        if (saveResult.canceled) {
            return;
        }

        let tempWindow = null;
        try {
            // Create temporary window for PDF generation
            tempWindow = new BrowserWindow({
                width: 794, 
                height: 1123,
                show: false,
                webPreferences: {
                    nodeIntegration: false,
                    contextIsolation: true
                }
            });

            // Load HTML content
            const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(data)}`;
            await tempWindow.loadURL(dataUrl);

            // Wait for content to fully load
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Generate PDF
            const pdfData = await tempWindow.webContents.printToPDF({
                marginsType: 0,
                pageSize: "A4",
                printBackground: true,
                landscape: false,
                preferCSSPageSize: false
            });

            // Save PDF file
            await fs.writeFile(saveResult.filePath, pdfData);
            
            return { status: 200, message: "success" };

        } finally {
            // Ensure cleanup
            if (tempWindow && !tempWindow.isDestroyed()) {
                tempWindow.close();
            }
        }
    }

    /**
    * Setup IPC handlers
    */
    setupIpcHandlers() {
        ipcMain.handle("generate-report", async (event, data, dataType) => {
            try {
                // Validate parameters
                this.validateReportParams(data, dataType);

                const parentWindow = BrowserWindow.fromWebContents(event.sender);
                if (!parentWindow) {
                    throw new Error('parent_window_not_found');
                }

                // Generate report based on type
                if (dataType === "json") {
                    return await this.generateJsonReport(data, parentWindow);
                } else {
                    return await this.generatePdfReport(data, parentWindow);
                }

            } catch (error) {
                console.error('Generate report error:', error);
                return {
                    status: 400,
                    message: error.message || "error"
                };
            }
        });

        // Handling PDF download
        ipcMain.on('download-manual', (event, downloadUrl) => {
            const win = BrowserWindow.fromWebContents(event.sender);
            if (win) {
                win.webContents.downloadURL(downloadUrl);
            }
        });
    }

    /**
     * Setup application event handlers
     */
    setupAppHandlers() {
        app.whenReady().then(() => {
            this.setupIpcHandlers();
            
            // Create window if server is ready, otherwise wait
            if (this.serverPort) {
                this.createWindow();
            } else {
                console.log('Waiting for server to start...');
            }
        });

        app.on("window-all-closed", () => {
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });

        app.on("activate", () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                this.createWindow();
            }
        });

        app.on("before-quit", () => {
            this.isQuitting = true;
        });

        app.on("quit", () => {
            if (this.serverProcess && !this.serverProcess.killed) {
                this.serverProcess.kill();
            }
        });
    }

    /**
     * Start the application
     */
    start() {
        this.initializeServer();
        this.setupAppHandlers();
    }
}

// Start the application
const electronApp = new ElectronApp();
electronApp.start();
