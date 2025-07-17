const emptyToast = () => ({
    toastStatus: null,
    toastClass: "",
    toastMessage: "",
});

export default () => ({

    initToast() {},

    toast: emptyToast(),
    
    toastVisible: false,
    
    toastTimeout: null,
    
    toastDuration: 3000,

    toastShow(toastStatus, toastMessage) {
        const toastClass = toastStatus < 400
            ? "bg-green-200 text-green-700"
            : "bg-red-200 text-red-700";
        this.toast = Object.assign(this.toast, { 
            toastStatus, 
            toastClass, 
            toastMessage: this.$t(`toast.${toastMessage}`)
        });
        this.toastVisible = true;
        this.toastTimeout = setTimeout(() => this.toastReset(), this.toastDuration);
    },

    toastSuccess(message = "success") {
        this.toastShow(200, message);
    },

    toastError(message = "error") {
        this.toastShow(400, message);
    },

    toastReset() {
        clearTimeout(this.toastTimeout);
        this.toastVisible = false;
        this.toast = emptyToast();
    },

    toastifyAppIsOnline() {
        this.$store.app.appIsOnline
            ? this.toastShow(200, "online")
            : this.toastShow(400, "offline");
    },

    toastifyPdfGeneration(response) {
        const { status: toastCode = 400, message: toastMessage = "error" } = response;
        toastCode == 200
            ? this.toastShow(200, "success")
            : this.toastShow(400, toastMessage);

    },

    toastContainer: {
        ["x-show"]: "toastVisible",

        [":class"]: "toast.toastClass",

        ["@click"]() {
            this.toastReset();
        }
    },

    toastMessage: {
        ["x-html"]: "toast.toastMessage"
    }
});
