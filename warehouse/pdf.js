// Add this to your web application's JavaScript
async function generatePDF() {
  if (window.electronAPI) {
    const result = await window.electronAPI.generatePDF();
    if (result.success) {
      console.log('PDF saved:', result.filePath);
    }
  }
}

async function generateAndOpenPDF() {
  if (window.electronAPI) {
    const result = await window.electronAPI.generateAndOpenPDF();
    if (result.success) {
      console.log('PDF generated and opened');
    }
  }
}
