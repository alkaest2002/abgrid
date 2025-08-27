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

        ["action"]() {
            this.navigationGoTo("multistep.data");
        }
    }
});
