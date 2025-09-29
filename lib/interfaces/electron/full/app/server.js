const http = require("http");
const fs = require("fs").promises;
const path = require("path");
const net = require("net");
const crypto = require("crypto");
const url = require("url");
const zlib = require("zlib");

const possiblePorts = [53472, 53247, 53274, 53427, 53724, 53742];
const publicDir = path.join(__dirname, "dist");

const mimeTypes = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".wav": "audio/wav",
    ".mp4": "video/mp4",
    ".woff": "application/font-woff",
    ".woff2": "font/woff2",
    ".ttf": "application/font-ttf",
    ".eot": "application/vnd.ms-fontobject",
    ".otf": "application/font-otf",
    ".wasm": "application/wasm",
    ".zip": "application/zip",
    ".ico": "image/x-icon"
};

// File types that benefit from gzip compression
const compressibleTypes = new Set([
    ".html", ".js", ".css", ".json", ".svg", ".txt", ".xml", ".csv"
]);

class StaticFileServer {
    constructor() {
        this.server = null;
        this.isShuttingDown = false;
        this.compressionCache = new Map(); // Cache compressed files
    }

    /**
     * Get safe file path, preventing path traversal attacks
     */
    getFilePath(requestUrl) {
        try {
            // Parse URL using modern URL constructor
            const parsedUrl = new URL(requestUrl, "http://localhost");
            const decodedPath = decodeURIComponent(parsedUrl.pathname);
            
            // Normalize path and check for traversal attempts
            const normalizedPath = path.normalize(decodedPath);
            
            // Remove leading slash and join with public directory
            const relativePath = normalizedPath.replace(/^\/+/, "");
            return path.join(publicDir, relativePath);
        } catch (error) {
            // Handle invalid URLs
            throw new Error("Invalid URL format");
        }
    }

    /**
     * Get content type based on file extension
     */
    getContentType(extname) {
        return mimeTypes[extname.toLowerCase()] || "application/octet-stream";
    }

    /**
     * Generate ETag for file
     */
    generateETag(stats, isCompressed = false) {
        const hash = crypto.createHash("md5");
        hash.update(`${stats.mtime.getTime()}-${stats.size}${isCompressed ? '-gzip' : ''}`);
        return `"${hash.digest("hex")}"`;
    }

    /**
     * Check if file should be compressed
     */
    shouldCompress(extname, acceptEncoding) {
        return acceptEncoding.includes('gzip') && compressibleTypes.has(extname.toLowerCase());
    }

    /**
     * Compress content using gzip
     */
    async compressContent(content, cacheKey) {
        return new Promise((resolve, reject) => {
            // Check cache first
            if (this.compressionCache.has(cacheKey)) {
                resolve(this.compressionCache.get(cacheKey));
                return;
            }

            zlib.gzip(content, { level: 6 }, (err, compressed) => {
                if (err) {
                    reject(err);
                    return;
                }
                
                // Cache the compressed content
                this.compressionCache.set(cacheKey, compressed);
                
                // Limit cache size to prevent memory issues
                if (this.compressionCache.size > 100) {
                    const firstKey = this.compressionCache.keys().next().value;
                    this.compressionCache.delete(firstKey);
                }
                
                resolve(compressed);
            });
        });
    }

    /**
     * Send error response
     */
    sendError(res, statusCode, message) {
        res.writeHead(statusCode, { 
            "Content-Type": "text/plain",
            "Cache-Control": "no-cache"
        });
        res.end(message);
    }

    /**
     * Handle HTTP requests
     */
    async handleRequest(req, res) {
        try {
            // Only allow GET and HEAD methods
            if (req.method !== "GET" && req.method !== "HEAD") {
                res.writeHead(405, { 
                    "Allow": "GET, HEAD",
                    "Content-Type": "text/plain" 
                });
                res.end("method_not_allowed");
                return;
            }

            // Get file path safely
            let filePath = this.getFilePath(req.url);
            
            // Check if file exists
            let stats;
            try {
                stats = await fs.stat(filePath);
            } catch (error) {
                if (error.code === "ENOENT") {
                    // File doesn't exist, try index.html for SPA routing
                    filePath = path.join(publicDir, "index.html");
                    try {
                        stats = await fs.stat(filePath);
                    } catch (indexError) {
                        this.sendError(res, 404, "404 Not Found");
                        return;
                    }
                } else {
                    throw error;
                }
            }

            // If it's a directory, serve index.html from that directory
            if (stats.isDirectory()) {
                filePath = path.join(filePath, "index.html");
                try {
                    stats = await fs.stat(filePath);
                } catch (error) {
                    if (error.code === "ENOENT") {
                        // No index.html in directory, fall back to main index.html
                        filePath = path.join(publicDir, "index.html");
                        stats = await fs.stat(filePath);
                    } else {
                        throw error;
                    }
                }
            }

            // Get content type and check compression
            const extname = path.extname(filePath);
            const contentType = this.getContentType(extname);
            const acceptEncoding = req.headers["accept-encoding"] || "";
            const shouldCompress = this.shouldCompress(extname, acceptEncoding);

            // Generate ETag
            const etag = this.generateETag(stats, shouldCompress);
            
            // Check if client has cached version
            const clientETag = req.headers["if-none-match"];
            if (clientETag === etag) {
                res.writeHead(304, {
                    "ETag": etag,
                    "Cache-Control": "public, max-age=3600"
                });
                res.end();
                return;
            }

            // Set base response headers
            const headers = {
                "Content-Type": contentType,
                "ETag": etag,
                "Cache-Control": "public, max-age=3600",
                "Last-Modified": stats.mtime.toUTCString(),
                "Vary": "Accept-Encoding"
            };

            // For HEAD requests, we need to set headers but not send content
            if (req.method === "HEAD") {
                if (shouldCompress) {
                    // We need to compress to get the correct content length for HEAD
                    const content = await fs.readFile(filePath);
                    const compressed = await this.compressContent(content, `${filePath}-${stats.mtime.getTime()}`);
                    headers["Content-Encoding"] = "gzip";
                    headers["Content-Length"] = compressed.length;
                } else {
                    headers["Content-Length"] = stats.size;
                }
                res.writeHead(200, headers);
                res.end();
                return;
            }

            // Read file content
            const content = await fs.readFile(filePath);

            // Compress if needed
            if (shouldCompress) {
                try {
                    const cacheKey = `${filePath}-${stats.mtime.getTime()}`;
                    const compressed = await this.compressContent(content, cacheKey);
                    
                    headers["Content-Encoding"] = "gzip";
                    headers["Content-Length"] = compressed.length;
                    
                    res.writeHead(200, headers);
                    res.end(compressed);
                } catch (compressionError) {
                    // Fallback to uncompressed if compression fails
                    console.warn(`Compression failed for ${filePath}:`, compressionError.message);
                    headers["Content-Length"] = stats.size;
                    res.writeHead(200, headers);
                    res.end(content);
                }
            } else {
                headers["Content-Length"] = stats.size;
                res.writeHead(200, headers);
                res.end(content);
            }

        } catch (error) {
            console.error("Request handling error:", error);
            if (error.code === "ENOENT") {
                this.sendError(res, 404, "404 Not Found");
            } else if (error.code === "EACCES") {
                this.sendError(res, 403, "403 Forbidden");
            } else {
                this.sendError(res, 500, "500 Internal Server Error");
            }
        }
    }

    /**
     * Check if a port is available
     */
    isPortAvailable(port) {
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
    }

    /**
     * Find the first available port
     */
    async findAvailablePort() {
        for (const port of possiblePorts) {
            const available = await this.isPortAvailable(port);
            if (available) {
                return port;
            }
        }
        throw new Error("No available ports found in the specified range");
    }

    /**
     * Setup graceful shutdown
     */
    setupGracefulShutdown() {
        const gracefulShutdown = (signal) => {
            console.log(`\nReceived ${signal}. Shutting down gracefully...`);
            this.isShuttingDown = true;
            
            if (this.server) {
                this.server.close(() => {
                    console.log("Server closed successfully");
                    // Clear compression cache
                    this.compressionCache.clear();
                    process.exit(0);
                });
                
                // Force close after 10 seconds
                setTimeout(() => {
                    console.log("Force closing server...");
                    process.exit(1);
                }, 10000);
            } else {
                process.exit(0);
            }
        };

        process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
        process.on("SIGINT", () => gracefulShutdown("SIGINT"));
    }

    /**
     * Start the server
     */
    async start() {
        try {
            // Check if public directory exists
            try {
                await fs.access(publicDir);
            } catch (error) {
                console.error(`Public directory '${publicDir}' does not exist`);
                process.exit(1);
            }

            const port = await this.findAvailablePort();
            this.server = http.createServer((req, res) => this.handleRequest(req, res));
            
            this.server.listen(port, () => {
                console.log(`Server is running on http://localhost:${port}`);
                console.log(`Serving files from: ${publicDir}`);
                console.log(`Gzip compression enabled for: ${Array.from(compressibleTypes).join(', ')}`);
                
                // Send the port back to the main process if running as child process
                if (process.send) {
                    process.send({ port });
                }
            });
            
            this.server.on("error", (error) => {
                console.error("Server error:", error);
                process.exit(1);
            });

            // Setup graceful shutdown
            this.setupGracefulShutdown();
            
        } catch (error) {
            console.error("Failed to start server:", error);
            process.exit(1);
        }
    }
}

// Start the server
const server = new StaticFileServer();
server.start();
