export async function downloadLink(url, filename) {
    return new Promise(async (resolve, reject) => {
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
            await downloadBlob(blob, filename);
            resolve(); // Resolve the promise on successful download
        } catch (error) {
            console.error('Download failed:', error);
            reject("download_failure"); // Reject with the specified message
        }
    });
}

const downloadBlob = (blob, filename) => {
    return new Promise((resolve, reject) => {
        try {
            // Create url object
            const objectUrl = URL.createObjectURL(blob);
            // Create link
            const link = document.createElement('a');
            // Configure link
            link.href = objectUrl;
            link.download = filename;
            
            // Add event listeners to handle success/failure
            link.addEventListener('click', () => {
                // Clean up after a short delay to allow download to start
                setTimeout(() => {
                    document.body.removeChild(link);
                    URL.revokeObjectURL(objectUrl);
                    resolve(); // Resolve when download is initiated
                }, 100);
            });
            
            // Append and click
            document.body.appendChild(link);
            link.click();
        } catch (error) {
            reject(error);
        }
    });
}
