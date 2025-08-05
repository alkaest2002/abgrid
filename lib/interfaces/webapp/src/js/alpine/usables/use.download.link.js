/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/

export async function downloadLink(url, filename) {
    // Fetch the file
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error("download_failure");
    }
    const blob = await response.blob();
    if (blob.size === 0) {
        throw new Error("download_failure");
    }
    if (window.showSaveFilePicker) {
        // Use modern API if available
        await saveWithModernAPI(blob, filename);
    } else {
        // Fallback to traditional method
        saveWithTraditionalMethod(blob, filename);
    }
}

// Modern File System Access API
async function saveWithModernAPI(blob, filename) {
    try {
        const fileHandle = await window.showSaveFilePicker({
            suggestedName: filename
        });
        const writable = await fileHandle.createWritable();
        await writable.write(blob);
        await writable.close();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('download_aborted');
        }
        throw error;
    }
}

// Traditional fallback method
function saveWithTraditionalMethod(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}
