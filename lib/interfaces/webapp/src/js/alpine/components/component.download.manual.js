/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { downloadLink } from "../usables/use.download.link";

export default () => ({

    initDownloadManual() {},

    downloadManualLink: {
        ["@click.prevent"]() {
            const pdfManualFilename = `${this.$store.app.appLanguage}.manual.pdf`;
            const pdfManualUrl = `${window.location.origin}/${pdfManualFilename}`;
            if (this.$store.app.appIsElectron) {
                window.electronAPI.downloadLink(pdfManualUrl);
            } else {
                downloadLink(pdfManualUrl, pdfManualFilename)
                    .then(() => this.toastShowSuccess("download_success"))
                    .catch(() => this.toastShowError("download_failure"));
            }
        }
    }
})