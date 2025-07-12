export function readFileWithLineLimit(file, maxLines) {
    return new Promise((resolve, reject) => {
        
        // 8KB chunks
        const chunkSize = 1024 * 8;
        let offset = 0;
        let content = "";
        let lineCount = 0;
        let buffer = "";
        
        // Init reader
        const reader = new FileReader();
        
        reader.onload = (evt) => {
            buffer += evt.target.result;
            
            // Split buffer in lines ending with a return
            const lines = buffer.split(/\r\n|\n|\r/);

            // Keep incomplete line in buffer
            buffer = lines.pop() || ""; 
            
            // Loop through lines
            for (const line of lines) {
                
                // Stop gracefully when max lines reached
                if (lineCount >= maxLines) {
                    return resolve(content);
                }
                // Add content                
                content += line + "\n";

                // Update line counter
                lineCount++;
            }
            
            // Continue reading if we haven't reached the limit or end of file
            if (offset < file.size && lineCount < maxLines) {
                readNextChunk();
            } else {
                // Add any remaining content
                resolve(content += buffer);
            }
        };
        
        // Handle reading errors
        reader.onerror = () => reject(new Error("file_load_failure"));
        
        // Chunks-reading function 
        const readNextChunk = () => {
            const blob = file.slice(offset, offset + chunkSize);
            offset += chunkSize;
            reader.readAsText(blob);
        };
        // Start chunks-reading
        readNextChunk();
    });
}
