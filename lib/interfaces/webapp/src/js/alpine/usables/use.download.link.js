export async function fetchAndDownload(url, filename) {
    try {
        // fetch url
        const response = await fetch(url);
        // Ensure the request was successful
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.statusText}`);
        }
        // Get the file data as a Blob
        const blob = await response.blob();
        // Use the helper function to download it
        downloadBlob(blob, filename);
    } catch (error) {
        console.error('Download failed:', error);
    }
}

function downloadBlob(blob, filename) {
    // Create url object
    const objectUrl = URL.createObjectURL(blob);
    // Create link
    const link = document.createElement('a');
    // Configure link
    link.href = objectUrl;
    link.download = filename;
    // Append, click and remove
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
}