const emptyToast = () => ({
    toastStatus: null,
    toastClass: "",
    toastMessage: "",
});

export default () => ({

    initToast() {},

    toast: emptyToast(),
    
    toastIsVisible: false,
    
    toastTimeout: null,
    
    toastDuration: 3000,

    toastShow(toastStatus, toastMessage) {
        const toastClass = toastStatus < 400
            ? "bg-green-100 text-green-700"
            : "bg-red-100 text-red-700";
        this.toast = Object.assign(this.toast, { 
            toastStatus, 
            toastClass, 
            toastMessage: this.$t(`toast.${toastMessage}`)
        });
        this.toastIsVisible = true;
        this.toastTimeout = setTimeout(() => this.toastReset(), this.toastDuration);
    },

    toastShowSuccess(message = "success") {
        this.toastShow(200, message);
    },

    toastShowError(message = "error") {
        this.toastShow(400, message);
    },

    toastReset() {
        clearTimeout(this.toastTimeout);
        this.toastIsVisible = false;
        this.toast = emptyToast();
    },

    toastifyReportGeneration(response) {
        const { status: toastCode = 400, message: toastMessage = "error" } = response;
        toastCode == 200
            ? this.toastShow(200, "success")
            : this.toastShow(400, toastMessage);

    },

    toastContainer: {
        ["x-show"]: "toastIsVisible",

        [":class"]: "toast.toastClass",

        ["@click"]() {
            this.toastReset();
        }
    },

    toastMessage: {
        ["x-html"]: "toast.toastMessage"
    }
});
