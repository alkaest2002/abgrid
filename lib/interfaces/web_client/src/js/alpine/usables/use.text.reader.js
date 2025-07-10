export function readFileWithLineLimit(file, maxLines) {
        return new Promise((resolve, reject) => {
            const chunkSize = 1024 * 8; // 8KB chunks
            let offset = 0;
            let content = '';
            let lineCount = 0;
            let buffer = '';
            
            const reader = new FileReader();
            
            reader.onload = (evt) => {
                buffer += evt.target.result;
                
                // Process complete lines
                const lines = buffer.split(/\r\n|\n|\r/);
                buffer = lines.pop() || ''; // Keep incomplete line in buffer
                
                for (const line of lines) {
                    content += line + '\n';
                    lineCount++;
                    
                    if (lineCount >= maxLines) {
                        return reject(new Error("file_exceeds_size_limit"));
                    }
                }
                
                // Continue reading if we haven't reached the limit or end of file
                if (offset < file.size && lineCount < maxLines) {
                    readNextChunk();
                } else {
                    // Add any remaining content
                    if (buffer) {
                        content += buffer;
                    }
                    resolve(content);
                }
            };
            
            reader.onerror = () => reject(new Error('file_load_failure'));
            
            const readNextChunk = () => {
                const blob = file.slice(offset, offset + chunkSize);
                offset += chunkSize;
                reader.readAsText(blob);
            };
            
            readNextChunk();
        });
    }