const http = require("http");
const fs = require("fs").promises;
const path = require("path");
const net = require("net");

const possiblePorts = [53472, 53247, 53274, 53427, 53724, 53742];
const publicDir = path.join(__dirname, "dist");

const mimeTypes = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".wav": "audio/wav",
    ".mp4": "video/mp4",
    ".woff": "application/font-woff",
    ".ttf": "application/font-ttf",
    ".eot": "application/vnd.ms-fontobject",
    ".otf": "application/font-otf",
    ".wasm": "application/wasm",
    ".zip": "application/zip",
};

const getFilePath = (url) => {
    let filePath = path.join(publicDir, url);
    return filePath;
};

const getContentType = (extname) => {
    return mimeTypes[extname.toLowerCase()] || "application/octet-stream";
};

const handleRequest = async (req, res) => {
    try {
        let filePath = getFilePath(req.url);
        
        // Check if the file exists and if it's a directory, serve index.html
        const stats = await fs.stat(filePath).catch(() => null);
        
        if (stats && stats.isDirectory()) {
            filePath = path.join(filePath, "index.html");
        }

        // Fallback to index.html if the file does not exist
        if (!stats) {
            filePath = path.join(publicDir, "index.html");
        }

        // Read the file
        const content = await fs.readFile(filePath);
        const extname = path.extname(filePath);
        const contentType = getContentType(extname);

        // Serve the file
        res.writeHead(200, {
            "Content-Type": contentType,
            "Cache-Control": "public, max-age=3600", // Cache static files for 1 hour
        });
        res.end(content, "utf-8");
    // On error
    } catch (error) {
        if (error.code === "ENOENT") {
            res.writeHead(404, { "Content-Type": "text/html" });
            res.end("404 Not Found", "utf-8");
        } else if (error.code === "EACCES") {
            res.writeHead(403, { "Content-Type": "text/html" });
            res.end("403 Forbidden", "utf-8");
        } else {
            res.writeHead(500, { "Content-Type": "text/plain" });
            res.end(`Server Error: ${error.message}`, "utf-8");
        }
    }
};

// Function to check if a port is available
const isPortAvailable = (port) => {
    return new Promise((resolve) => {
        const server = net.createServer();
        
        server.listen(port, () => {
            server.once("close", () => {
                resolve(true);
            });
            server.close();
        });
        
        server.on("error", () => {
            resolve(false);
        });
    });
};

// Function to find the first available port
const findAvailablePort = async () => {
    for (const port of possiblePorts) {
        const available = await isPortAvailable(parseInt(port));
        if (available) {
            return parseInt(port);
        }
    }
    throw new Error("No available ports found in the specified range");
};

// Start the server
const startServer = async () => {
    try {
        const port = await findAvailablePort();
        const server = http.createServer(handleRequest);
        
        server.listen(port, () => {
            console.log(`Server is running on http://localhost:${port}`);
            // Send the port back to the main process
            process.send({ port });
        });
        
        server.on("error", (error) => {
            console.error("Server error:", error);
            process.exit(1);
        });
        
    } catch (error) {
        console.error("Failed to start server:", error);
        process.exit(1);
    }
};

startServer();
