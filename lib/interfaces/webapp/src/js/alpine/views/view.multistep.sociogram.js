/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export default () => ({

    init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);

        // Get questions
        this.questionA = this.$store.api.apiResponse?.data?.detail?.group_data?.question_a;
        this.questionB = this.$store.api.apiResponse?.data?.detail?.group_data?.question_b;
    },

    questionA: null,

    questionB: null,

    withSociogram: false,

    magicButton: {

        ["label"]: "next",

        async ["action"]() {
            // Get data to send
            const bodyData = JSON.parse(
                JSON.stringify(
                    this.$store.data.dataMultiStep.step1
                )
            )
            // Try api
            try {
                // Create api request
                const apiRequest = {
                    endpoint: "api/report/step_2",
                    method: "POST",
                    queryParams: { with_sociogram: this.withSociogram },
                    bodyData
                };
                // Make api request to server
                const { statusCode } = await this.apiProcessRequest(apiRequest);

                // On api success
                if (statusCode == 200) {
                    // Navigate to appropriate page
                    this.navigationGoTo("multistep.data")
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
