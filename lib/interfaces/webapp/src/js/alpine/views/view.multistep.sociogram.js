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
            try {
                // Create api request
                const apiRequest = {
                    endpoint: "api/report/step_1",
                    method: "POST",
                    queryParams: {
                        with_sociogram: this.withSociogram
                    },
                    bodyData: JSON.parse(JSON.stringify(convertYAMLToJSON))
                };
                // Make api request to server
                const { statusCode } = await this.apiProcessRequest(apiRequest);

                // On api success
                if (statusCode == 200) {
                    // Navigate to appropriate page
                    this.navigationGoTo(this.goTo)
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
                // YAML error
                if ("name" in error && error.name == "YAMLParseError") {
                    // Save YAML error to store
                    this.$store.data.dataYAMLError = error;
                    // Toast error
                    this.toastShowError("file_invalid_yaml");
                    // Go to notify
                    this.navigationGoTo("notify.error.yaml");
                    // Api error
                } else {
                    this.navigationGoTo("notify.error.api");
                }
            }
        }
    }
});
