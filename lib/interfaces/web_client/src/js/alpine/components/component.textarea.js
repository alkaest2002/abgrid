export default (content) => ({

    textareaContent: "",
    textareaLines: [1],
    textareaPendingUpdate: false,

    init() {
        this.textareaContent = content;
        this.$watch("textareaContent", () => {
            // Only reset scroll to top if this is a completely new content load
            // (not just minor edits by the user)
            if (this.textareaContent !== content) {
                this.$nextTick(() => {
                    this.$refs.textareaInputField.scrollTop = 0;
                    this.textareaSyncScroll();
                });
            }
            this.textareaThrottledUpdateLines();
        });
        this.textareaUpdateLines();
    },

    textareaHandleInput() {
        this.textareaThrottledUpdateLines();
    },

    textareaThrottledUpdateLines() {
        if (this.textareaPendingUpdate) return;
        this.textareaPendingUpdate = true;
        requestAnimationFrame(() => {
            this.textareaUpdateLines();
            this.textareaPendingUpdate = false;
        });
    },

    textareaUpdateLines() {
        const lineCount = this.textareaContent.split('\n').length || 1;
        this.textareaLines = Array.from({ length: lineCount }, (_, i) => i + 1);
    },

    textareaSyncScroll() {
        const inputField = this.$refs.textareaInputField;
        const lineNumbers = this.$refs.textareaLineNumbers;

        // Force sync
        lineNumbers.scrollTop = inputField.scrollTop;

        // Double-check sync worked
        requestAnimationFrame(() => {
            if (Math.abs(lineNumbers.scrollTop - inputField.scrollTop) > 1) {
                lineNumbers.scrollTop = inputField.scrollTop;
            }
        });
    },


    textareaLineNumbers: {
        ["x-ref"]: "textareaLineNumbers",
    },

    textareaInputField: {
        ["x-ref"]: "textareaInputField",

        ["x-model"]: "textareaContent",

        ["@input"]() {
            this.textareaHandleInput();
        },

        ["@scroll"]() {
            this.textareaSyncScroll();
        }
    }
});
