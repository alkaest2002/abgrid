const http = require('http');
const fs = require('fs').promises;
const path = require('path');

const port = 53472;
const publicDir = path.join(__dirname, 'dist');

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.wav': 'audio/wav',
    '.mp4': 'video/mp4',
    '.woff': 'application/font-woff',
    '.ttf': 'application/font-ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.otf': 'application/font-otf',
    '.wasm': 'application/wasm',
    '.zip': 'application/zip',
};

const getFilePath = (url) => {
    let filePath = path.join(publicDir, url);
    return filePath;
};

const getContentType = (extname) => {
    return mimeTypes[extname.toLowerCase()] || 'application/octet-stream';
};

const handleRequest = async (req, res) => {
    try {
        let filePath = getFilePath(req.url);
        
        // check if the file exists and if it’s a directory, serve index.html
        const stats = await fs.stat(filePath).catch(() => null);
        
        if (stats && stats.isDirectory()) {
            filePath = path.join(filePath, 'index.html');
        }

        // fallback to index.html if the file does not exist
        if (!stats) {
            filePath = path.join(publicDir, 'index.html');
        }

        // read the file
        const content = await fs.readFile(filePath);
        const extname = path.extname(filePath);
        const contentType = getContentType(extname);

        res.writeHead(200, {
            'Content-Type': contentType,
            'Cache-Control': 'public, max-age=3600', // Cache static files for 1 hour
        });
        res.end(content, 'utf-8');
    } catch (error) {
        if (error.code === 'ENOENT') {
            res.writeHead(404, { 'Content-Type': 'text/html' });
            res.end('404 Not Found', 'utf-8');
        } else if (error.code === 'EACCES') {
            res.writeHead(403, { 'Content-Type': 'text/html' });
            res.end('403 Forbidden', 'utf-8');
        } else {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end(`Server Error: ${error.message}`, 'utf-8');
        }
    }
};

const server = http.createServer(handleRequest);

server.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
