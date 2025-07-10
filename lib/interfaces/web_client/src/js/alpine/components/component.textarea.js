export default (content) => ({

    textareaContent: "",
    textareaLines: [1],
    textareaPendingUpdate: false,
    scrollPendingUpdate: false,

    init() {
        this.textareaContent = content;
        this.$watch("textareaContent", () => {
            this.textareaThrottledUpdateLines();
        });
        this.textareaUpdateLines();
    },

    textareaUpdateLines() {
        const lineCount = this.textareaContent.split('\n').length || 1;
        this.textareaLines = Array.from({ length: lineCount }, (_, i) => i + 1);
    },

    textareaThrottledUpdateLines() {
        if (this.textareaPendingUpdate) return;
        this.textareaPendingUpdate = true;
        requestAnimationFrame(() => {
            this.textareaUpdateLines();
            this.textareaPendingUpdate = false;
        });
    },

    textareaThrottledSyncScroll() {
        if (this.scrollPendingUpdate) return;
        this.scrollPendingUpdate = true;
        requestAnimationFrame(() => {
            this.$refs.textareaLineNumbers.scrollTop = 
                this.$refs.textareaInputField.scrollTop;
            this.scrollPendingUpdate = false;
        });
    },

    textareaLineNumbers: {
        ["x-ref"]: "textareaLineNumbers",
    },

    textareaInputField: {
        ["x-ref"]: "textareaInputField",

        ["x-model"]: "textareaContent",

        ["@input"]() {
            this.textareaThrottledUpdateLines();
            this.$dispatch("textarea:input", this.textareaContent);
        },

        ["@scroll"]() {
            this.textareaThrottledSyncScroll();
        }
    }
});
