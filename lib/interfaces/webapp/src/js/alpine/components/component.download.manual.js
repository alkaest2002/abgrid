/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { downloadLink } from "../usables/use.download.link";

export default () => ({

    initDownloadManual() {}, 

    downloadManualLink: {
        async ["@click.prevent"]() {
            const pdfManual = `${this.$store.app.appLanguage}.manual.pdf`;
            const pdfManualUrl = `${window.location.origin}/${pdfManual}`;
            if (this.$store.app.appIsElectron) {
                window.electronAPI.downloadLink(pdfManualUrl);
            } else {
                await downloadLink(pdfManualUrl, pdfManual);
            }
        }
    }
})