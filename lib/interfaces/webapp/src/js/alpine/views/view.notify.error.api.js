/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export default () => ({

    init() {
        this.$nextTick(() => {
            // Unlock magic button
            this.$store.app.appMagicButtonIsLocked = false;

            // Get api status code
            const { statusCode } = this.$store.api.apiResponse;

            // Save status code
            this.statusCode = statusCode;
        });
    },

    statusCode: 400,

    get notifyErrorApi() {
        return this.$store.api.apiResponse?.data?.detail;
    },

    magicButton: {

        ["label"]: "prev",

        ["action"]() {
            this.statusCode in [401, 403] 
                ? this.navigationGoTo("/")
                : this.navigationGoTo("dropzone.data");
        }
    }
});
