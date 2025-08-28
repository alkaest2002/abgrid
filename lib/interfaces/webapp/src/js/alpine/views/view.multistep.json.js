/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export default () => ({

    init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
    },

    multistepJSONSpinner: false,


    multistepDownloadLinkFactoryJSON() {
        return this.$store.app.appIsElectron
            // Electron app
            ? {
                    async ["@click.prevent"]() {
                        const data = this.$store.data.dataMultiStep.step2.encoded_data
                        this.multistepJSONSpinner = true;
                        const response = await window.electronAPI.generateReport(data, "json");
                        response && this.toastifyReportGeneration(response);
                        this.multistepJSONSpinner = false;
                    }
                }
            // Web app
            : {
                    ["@click.prevent"]() {
                        const data = this.$store.data.dataMultiStep.step2.encoded_data
                        const type = "application/json";
                        const fileExtension = "json";
                        this.multistepJSONSpinner = true;
                        const blob = new Blob([data], { type });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `abgrid-report.${fileExtension}`;
                        a.click();
                        URL.revokeObjectURL(url);
                        this.multistepJSONSpinner = false;
                    }
                }
    },

    magicButton: {

        ["label"]: "next",

        async ["action"]() {
            // Get data to send
            const bodyData = JSON.parse(
                JSON.stringify(
                    this.$store.data.dataMultiStep.step2
                )
            )
            // Try api
            try {
                // Create api request
                const apiRequest = {
                    endpoint: "api/report/step_3",
                    method: "POST",
                    bodyData,
                    queryParams: { 
                        "language": this.$store.app.appLanguage, 
                    },
                };
                // Make api request to server
                const { statusCode, data: { detail }} = await this.apiProcessRequest(apiRequest);
                // On api success
                if (statusCode == 200) {
                    // Save api response to store
                    this.$store.data.dataMultiStep.step3 = detail;
                    // Navigate to appropriate page
                    this.navigationGoTo("multistep.report")
                    // On api queue error
                } else if (statusCode == 429) {
                    // Navigate to queue notification page
                    this.navigationGoTo("notify.queue");
                    // On any other api error
                } else {
                    // Navigate to error api notification page
                    this.navigationGoTo("notify.error.api");
                }
                // On error
            } catch (error) {
                this.navigationGoTo("notify.error.api");
            }
        }
    }
});
