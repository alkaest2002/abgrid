export default (content) => ({

    textareaContent: "",
    textareaLines: [1],
    textareaPendingUpdate: false,
    textareaScrollPendingUpdate: false,
    textareaIsDisabled: false,

    init() {
        // Populate textarea with content
        this.textareaContent = content;
        
        // Listen for changes in textarea content
        this.$watch("textareaContent", () => {
            // Update line numbers
            this.textareaThrottledUpdateLines();
        });
        // Update line numbers right away
        this.textareaUpdateLines();
    },

    textareaUpdateLines() {
        // Count hnumber of lines in content
        const lineCount = this.textareaContent.split('\n').length || 1;
        // Create line numbers
        this.textareaLines = Array.from({ length: lineCount }, (_, i) => i + 1);
    },

    textareaThrottledUpdateLines() {
        // Update line numbers in sync with animation frames
        if (this.textareaPendingUpdate) return;
        this.textareaPendingUpdate = true;
        requestAnimationFrame(() => {
            this.textareaUpdateLines();
            this.textareaPendingUpdate = false;
        });
    },

    textareaThrottledSyncScroll() {
        // Scroll line numbers to match textarea scroll position in sync with animation frames
        if (this.textareaScrollPendingUpdate) return;
        this.textareaScrollPendingUpdate = true;
        requestAnimationFrame(() => {
            this.$refs.textareaLineNumbers.scrollTop = 
                this.$refs.textareaInputField.scrollTop;
            this.textareaScrollPendingUpdate = false;
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
