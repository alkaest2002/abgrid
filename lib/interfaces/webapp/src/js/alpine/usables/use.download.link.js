/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/

export async function downloadLink(input, filename) {
    // Init var
    let blob;
    
    // Check if input is already a Blob
    if (input instanceof Blob) {
        blob = input;
    
    // Input is a URL, fetch it
    } else if (typeof input === "string") {
        const response = await fetch(input);
        if (!response.ok) {
            throw new Error("download_failure");
        }
        blob = await response.blob();
    } else {
        throw new Error("download_failure");
    }
    
    // Validate blob
    if (blob.size === 0) {
        throw new Error("download_failure");
    }
    
    // Download using appropriate method
    if (window.showSaveFilePicker) {
        // Use modern API if available
        await saveWithModernAPI(blob, filename);
    } else {
        // Fallback to traditional method
        saveWithTraditionalMethod(blob, filename);
    }
}

// Traditional fallback method
export function saveWithTraditionalMethod(blob, filename) {
    
    // Create fake link and click it
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    queueMicrotask(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    });
}

// Modern File System Access API
export async function saveWithModernAPI(blob, filename) {
    try {
        const fileHandle = await window.showSaveFilePicker({
            suggestedName: filename
        });
        const writable = await fileHandle.createWritable();
        await writable.write(blob);
        await writable.close();
    } catch (error) {
        if (error.name === "AbortError") {
            throw new Error("download_aborted");
        }
        throw error;
    }
}
