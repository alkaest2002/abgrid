class YAMLToJSONConverter {
    constructor() {
        this.fileInput = document.getElementById('fileInput');
        this.convertBtn = document.getElementById('convertBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.yamlOutput = document.getElementById('yamlOutput');
        this.jsonOutput = document.getElementById('jsonOutput');
        this.fileInfo = document.getElementById('fileInfo');
        this.messages = document.getElementById('messages');
        
        this.currentFile = null;
        this.yamlContent = '';
        this.jsonContent = '';
        
        this.initializeEventListeners();
    }

    /**
     * Initialize all event listeners
     */
    initializeEventListeners() {
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.convertBtn.addEventListener('click', () => this.convertYAMLToJSON());
        this.downloadBtn.addEventListener('click', () => this.downloadJSON());
        this.clearBtn.addEventListener('click', () => this.clearAll());
        
        // Drag and drop functionality
        this.setupDragAndDrop();
    }

    /**
     * Handle file selection from input
     * @param {Event} event - File input change event
     */
    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) {
            this.clearAll();
            return;
        }

        if (!this.validateFile(file)) {
            return;
        }

        this.currentFile = file;
        await this.readFile(file);
    }

    /**
     * Validate selected file
     * @param {File} file - Selected file
     * @returns {boolean} - Whether file is valid
     */
    validateFile(file) {
        const validExtensions = ['.yaml', '.yml'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (!validExtensions.includes(fileExtension)) {
            this.showMessage('Please select a valid YAML file (.yaml or .yml)', 'error');
            return false;
        }

        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            this.showMessage('File size must be less than 10MB', 'error');
            return false;
        }

        return true;
    }

    /**
     * Read file content using FileReader
     * @param {File} file - File to read
     */
    async readFile(file) {
        try {
            this.showFileInfo(file);
            this.showMessage('Reading file...', 'info');

            const content = await this.readFileAsText(file);
            this.yamlContent = content;
            this.yamlOutput.textContent = content;
            
            this.convertBtn.disabled = false;
            this.showMessage('File loaded successfully!', 'success');
            
        } catch (error) {
            this.showMessage(`Error reading file: ${error.message}`, 'error');
            this.clearOutputs();
        }
    }

    /**
     * Read file content as text using Promise-based FileReader
     * @param {File} file - File to read
     * @returns {Promise<string>} - File content as string
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (event) => {
                resolve(event.target.result);
            };
            
            reader.onerror = (event) => {
                reject(new Error('Failed to read file'));
            };
            
            reader.onabort = (event) => {
                reject(new Error('File reading was aborted'));
            };
            
            // Read file as text
            reader.readAsText(file, 'UTF-8');
        });
    }

    /**
     * Convert YAML content to JSON
     */
    convertYAMLToJSON() {
        if (!this.yamlContent) {
            this.showMessage('No YAML content to convert', 'error');
            return;
        }

        try {
            this.showMessage('Converting YAML to JSON...', 'info');
            
            // Parse YAML using js-yaml library
            const yamlObject = jsyaml.load(this.yamlContent, {
                schema: jsyaml.DEFAULT_SCHEMA,
                json: true // Enable JSON compatibility mode
            });
            
            // Convert to formatted JSON string
            this.jsonContent = JSON.stringify(yamlObject, null, 2);
            
            // Display JSON output
            this.jsonOutput.textContent = this.jsonContent;
            
            this.downloadBtn.disabled = false;
            this.showMessage('Conversion successful!', 'success');
            
        } catch (error) {
            this.showMessage(`YAML parsing error: ${error.message}`, 'error');
            this.jsonOutput.textContent = 'Conversion failed';
            this.downloadBtn.disabled = true;
        }
    }

    /**
     * Download JSON content as file
     */
    downloadJSON() {
        if (!this.jsonContent) {
            this.showMessage('No JSON content to download', 'error');
            return;
        }

        try {
            const blob = new Blob([this.jsonContent], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const originalName = this.currentFile.name;
            const jsonFileName = originalName.replace(/\.(yaml|yml)$/i, '.json');
            
            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = jsonFileName;
            downloadLink.style.display = 'none';
            
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            URL.revokeObjectURL(url);
            this.showMessage(`JSON file downloaded as ${jsonFileName}`, 'success');
            
        } catch (error) {
            this.showMessage(`Download failed: ${error.message}`, 'error');
        }
    }

    /**
     * Setup drag and drop functionality
     */
    setupDragAndDrop() {
        const dropZone = document.querySelector('.file-input');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.backgroundColor = '#e3f2fd';
                dropZone.style.border = '2px dashed #2196f3';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.backgroundColor = '';
                dropZone.style.border = '2px dashed #ddd';
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.fileInput.files = files;
                this.handleFileSelect({ target: { files: files } });
            }
        }, false);
    }

    /**
     * Prevent default drag behaviors
     * @param {Event} e - Drag event
     */
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    /**
     * Show file information
     * @param {File} file - Selected file
     */
    showFileInfo(file) {
        const formatBytes = (bytes) => {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };

        this.fileInfo.innerHTML = `
            <strong>File:</strong> ${file.name}<br>
            <strong>Size:</strong> ${formatBytes(file.size)}<br>
            <strong>Type:</strong> ${file.type || 'application/x-yaml'}<br>
            <strong>Last Modified:</strong> ${new Date(file.lastModified).toLocaleString()}
        `;
        this.fileInfo.style.display = 'block';
    }

    /**
     * Show message to user
     * @param {string} message - Message text
     * @param {string} type - Message type (success, error, info)
     */
    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = type;
        messageDiv.textContent = message;
        
        this.messages.innerHTML = '';
        this.messages.appendChild(messageDiv);
        
        // Auto-remove info messages after 3 seconds
        if (type === 'info') {
            setTimeout(() => {
                if (this.messages.contains(messageDiv)) {
                    this.messages.removeChild(messageDiv);
                }
            }, 3000);
        }
    }

    /**
     * Clear all outputs and reset
     */
    clearAll() {
        this.fileInput.value = '';
        this.currentFile = null;
        this.yamlContent = '';
        this.jsonContent = '';
        
        this.clearOutputs();
        this.fileInfo.style.display = 'none';
        this.messages.innerHTML = '';
        
        this.convertBtn.disabled = true;
        this.downloadBtn.disabled = true;
    }

    /**
     * Clear output displays
     */
    clearOutputs() {
        this.yamlOutput.textContent = 'No file selected';
        this.jsonOutput.textContent = 'No conversion performed';
    }
}

// Initialize the converter when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YAMLToJSONConverter();
});
