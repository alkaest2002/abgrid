const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const fs = require("fs").promises;
const os = require("os");

const RENDER_APP_URL = "https://abgrid-webapp.onrender.com";
const AMPLIFY_APP_URL = "https://main.d2uoduro0n2rfk.amplifyapp.com";
const CLOUDFLARE_APP_URL = "https://abgrid-webapp.p-calanna.workers.dev";

class ElectronApp {
    constructor() {
        this.mainWindow = null;
        this.isQuitting = false;
        this.webAppUrl = CLOUDFLARE_APP_URL;
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

        // Load the remote web app
        this.mainWindow.loadURL(this.webAppUrl);
        
        // Handle window closed
        this.mainWindow.on("closed", () => {
            this.mainWindow = null;
        });

        // Prevent user from resizing window
        this.mainWindow.on("will-resize", (event) => {
            event.preventDefault();
        });

        // Handle navigation to ensure we stay within the app domain
        this.mainWindow.webContents.on("will-navigate", (event, navigationUrl) => {
            const url = new URL(navigationUrl);
            const appUrl = new URL(this.webAppUrl);
            
            // Allow navigation within the same domain
            if (url.origin !== appUrl.origin) {
                event.preventDefault();
                // Optionally open external links in default browser
                require("electron").shell.openExternal(navigationUrl);
            }
        });

        // Handle new window requests
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            const urlObj = new URL(url);
            const appUrl = new URL(this.webAppUrl);
            
            // Allow same-origin popups, deny others or open in browser
            if (urlObj.origin === appUrl.origin) {
                return { action: "allow" };
            } else {
                require("electron").shell.openExternal(url);
                return { action: "deny" };
            }
        });

        // Handle loading errors
        this.mainWindow.webContents.on("did-fail-load", (event, errorCode, errorDescription, validatedURL) => {
            if (errorCode !== -3) { // -3 is ERR_ABORTED, which is normal
                console.error(`Failed to load: ${errorDescription} (${errorCode})`);
                this.showErrorDialog("Connection Error", 
                    "Failed to connect to AB-Grid web app. Please check your internet connection.");
            }
        });
        
        // Uncomment for development
        // this.mainWindow.webContents.openDevTools();
    }

    /**
     * Validate report generation parameters
     */
    validateReportParams(data, dataType) {
        if (!data || typeof data !== "string") {
            throw new Error("invalid_data");
        }

        if (!["json", "html", "pdf"].includes(dataType)) {
            throw new Error("invalid_data_type");
        }

        if (data.length === 0) {
            throw new Error("empty_data_provided");
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
            return {
                status: 400,
                message: "generation_aborted"
            };
        }

        const fileData = Buffer.from(data, "utf8");
        await fs.writeFile(saveResult.filePath, fileData);
        
        return { status: 200, message: "generation_success" };
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
            return {
                status: 400,
                message: "generation_aborted"
            };
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
            
            return { status: 200, message: "generation_success" };

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
                    throw new Error("parent_window_not_found");
                }

                // Generate report based on type
                if (dataType === "json") {
                    return await this.generateJsonReport(data, parentWindow);
                } else {
                    return await this.generatePdfReport(data, parentWindow);
                }

            } catch (error) {
                console.error("Generate report error:", error);
                return {
                    status: 400,
                    message: error.message || "generation_failure"
                };
            }
        });

        // Handle get Electron version
        ipcMain.handle("electron-version", () => {
            return process.versions.electron;
        });

        // Handle PDF download
        ipcMain.handle("download-link", (event, downloadUrl) => {
            const win = BrowserWindow.fromWebContents(event.sender);
            win && win.webContents.downloadURL(downloadUrl);
        });
    }

    /**
     * Setup application event handlers
     */
    setupAppHandlers() {
        app.whenReady().then(() => {
            this.setupIpcHandlers();
            this.createWindow();
        });

        app.on("window-all-closed", () => {
            if (process.platform !== "darwin") {
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
    }

    /**
     * Start the application
     */
    start() {
        this.setupAppHandlers();
    }
}

// Start the application
const electronApp = new ElectronApp();
electronApp.start();
