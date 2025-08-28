/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/

export default () => ({

    init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);

        // Get questions from dataYAML
        this.multistepQuestionA = this.$store.data.dataYAML.match(/question_a:(.*?)(?=\?)/msu)?.[1]?.trim() + "?";
        this.multistepQuestionB = this.$store.data.dataYAML.match(/question_b:(.*?)(?=\?)/msu)?.[1]?.trim() + "?";
    },

    multistepQuestionA: null,

    multistepQuestionB: null,

    multistepWithSociogram: false,

    magicButton: {

        ["label"]: "next",

        async ["action"]() {
            // Get data to send
            const bodyData = JSON.parse(JSON.stringify(this.$store.data.dataMultiStep.step1));
            // Try api
            try {
                // Create api request
                const apiRequest = {
                    endpoint: "api/report/step_2",
                    method: "POST",
                    queryParams: { with_sociogram: this.multistepWithSociogram },
                    bodyData
                };
                // Make api request to server
                const { statusCode, data: { detail }} = await this.apiProcessRequest(apiRequest);

                // On api success
                if (statusCode == 200) {
                    // Save api response to store
                    this.$store.data.dataMultiStep.step2 = detail;
                    // Navigate to appropriate page
                    this.navigationGoTo("multistep.json")
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
