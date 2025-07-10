export default (content) => ({

    textareaContent: "",
    textareaLines: [1],
    textareaPendingUpdate: false,

    init() {
        this.textareaContent = content;
        this.$watch("textareaContent", () => this.textareaThrottledUpdateLines());
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
        this.$refs.textareaLineNumbers.scrollTop = this.$refs.textareaInputField.scrollTop;
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