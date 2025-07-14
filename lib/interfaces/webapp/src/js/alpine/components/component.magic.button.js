export default (label, action) => ({

    magicButtonIsSpinning: false,

    magicButtonMetaKeyIsPressed: false,

    magicButtonClasses: "h-18 w-18 rounded-full text-sm font-medium text-white border shadow-sm inline-flex justify-center items-center",

    magicButtonIcons: {

        "home": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-5" viewBox="0 0 576 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M575.8 255.5c0 18-15 32.1-32 32.1l-32 0 .7 160.2c0 2.7-.2 5.4-.5 8.1l0 16.2c0 22.1-17.9 40-40 40l-16 0c-1.1 0-2.2 0-3.3-.1c-1.4 .1-2.8 .1-4.2 .1L416 512l-24 0c-22.1 0-40-17.9-40-40l0-24 0-64c0-17.7-14.3-32-32-32l-64 0c-17.7 0-32 14.3-32 32l0 64 0 24c0 22.1-17.9 40-40 40l-24 0-31.9 0c-1.5 0-3-.1-4.5-.2c-1.2 .1-2.4 .2-3.6 .2l-16 0c-22.1 0-40-17.9-40-40l0-112c0-.9 0-1.9 .1-2.8l0-69.7-32 0c-18 0-32-14-32-32.1c0-9 3-17 10-24L266.4 8c7-7 15-8 22-8s15 2 21 7L564.8 231.5c8 7 12 15 11 24z"/></svg>`,

        "next": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-6" viewBox="0 0 256 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M246.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-9.2-9.2-22.9-11.9-34.9-6.9s-19.8 16.6-19.8 29.6l0 256c0 12.9 7.8 24.6 19.8 29.6s25.7 2.2 34.9-6.9l128-128z"/></svg>`,

        "prev": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-6" viewBox="0 0 256 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M9.4 278.6c-12.5-12.5-12.5-32.8 0-45.3l128-128c9.2-9.2 22.9-11.9 34.9-6.9s19.8 16.6 19.8 29.6l0 256c0 12.9-7.8 24.6-19.8 29.6s-25.7 2.2-34.9-6.9l-128-128z"/></svg>`,

        "spinner": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="animate-spin h-6" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M304 48a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zm0 416a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zM48 304a48 48 0 1 0 0-96 48 48 0 1 0 0 96zm464-48a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zM142.9 437A48 48 0 1 0 75 369.1 48 48 0 1 0 142.9 437zm0-294.2A48 48 0 1 0 75 75a48 48 0 1 0 67.9 67.9zM369.1 437A48 48 0 1 0 437 369.1 48 48 0 1 0 369.1 437z"/></svg>`
    },

    magicButton: {

        [":class"]() {
            const isDisabled = this.$store.app.magicButtonIsLocked
                ? "opacity-25 cursor-not-allowed"
                : "cursor-pointer";
            const isDisabledMeta = this.$store.api.apiRequestIsPending
                ? "opacity-25 cursor-not-allowed"
                : "cursor-pointer";
            return this.magicButtonMetaKeyIsPressed 
                ? `${isDisabledMeta} bg-purple-700 border-purple-700 shadow-purple-900 cursor-pointer ${this.magicButtonClasses}`
                : `${isDisabled} bg-blue-700 border-blue-700 shadow-blue-900 ${this.magicButtonClasses}`
        },

        ["x-html"]() {
            const actualLabel = label instanceof Function
                ? label.call(this)
                : label;
            return this.magicButtonIsSpinning
                ? this.magicButtonIcons["spinner"]
                : this.magicButtonMetaKeyIsPressed
                    ? this.magicButtonIcons["home"]
                    : actualLabel in this.magicButtonIcons
                        ? this.magicButtonIcons[actualLabel]
                        : actualLabel;
        },

        async ["@click"]({ metaKey }) {
            // Override magic button action if meta key is pressed
            // Provided there are no pending api requests
            if (metaKey && !this.$store.api.apiRequestIsPending) {
                // Unlock magic button
                this.$store.app.magicButtonIsLocked = false;
                // Always go home
                return this.navigationGoTo("/");
            }
            // Do nothing if magic button is locked or api request is pending
            if (this.$store.app.magicButtonIsLocked || this.$store.api.apiRequestIsPending)
                return;
            // Lock magic button
            this.$store.app.magicButtonIsLocked = true;
            // Spin magic button
            this.magicButtonIsSpinning = true;
            try {
                // Reset toast queue
                this.toastReset();
                // Do magic button action
                await action.call(this);
            } finally {
                // Stop magic button from spinning
                this.magicButtonIsSpinning = false;
                // Unlock magic button
                this.$store.app.magicButtonIsLocked = false;
            }
        },

        ["@keyup.meta.window"]() {
            this.magicButtonMetaKeyIsPressed = false;
        },

         ["@keydown.meta.window"]() {
            this.magicButtonMetaKeyIsPressed = true;
        },
    }
});