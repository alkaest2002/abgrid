export default (label, action, customClasses = "bg-blue-700 border-blue-700") => ({

    magicButtonAnimation: false,

    magicButtonMetaKeyIsPressed: false,

    magicButtonInitialClasses: "h-12 w-12 rounded-full text-sm font-medium text-white border shadow-sm inline-flex justify-center items-center cursor-pointer",

    magicButtonCurrentIcon: null,

    magicButtonIcons: {

        "home": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-5" viewBox="0 0 576 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M575.8 255.5c0 18-15 32.1-32 32.1l-32 0 .7 160.2c0 2.7-.2 5.4-.5 8.1l0 16.2c0 22.1-17.9 40-40 40l-16 0c-1.1 0-2.2 0-3.3-.1c-1.4 .1-2.8 .1-4.2 .1L416 512l-24 0c-22.1 0-40-17.9-40-40l0-24 0-64c0-17.7-14.3-32-32-32l-64 0c-17.7 0-32 14.3-32 32l0 64 0 24c0 22.1-17.9 40-40 40l-24 0-31.9 0c-1.5 0-3-.1-4.5-.2c-1.2 .1-2.4 .2-3.6 .2l-16 0c-22.1 0-40-17.9-40-40l0-112c0-.9 0-1.9 .1-2.8l0-69.7-32 0c-18 0-32-14-32-32.1c0-9 3-17 10-24L266.4 8c7-7 15-8 22-8s15 2 21 7L564.8 231.5c8 7 12 15 11 24z"/></svg>`,

        "next": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-5" viewBox="0 0 256 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M246.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-9.2-9.2-22.9-11.9-34.9-6.9s-19.8 16.6-19.8 29.6l0 256c0 12.9 7.8 24.6 19.8 29.6s25.7 2.2 34.9-6.9l128-128z"/></svg>`,

        "prev": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-5" viewBox="0 0 256 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M9.4 278.6c-12.5-12.5-12.5-32.8 0-45.3l128-128c9.2-9.2 22.9-11.9 34.9-6.9s19.8 16.6 19.8 29.6l0 256c0 12.9-7.8 24.6-19.8 29.6s-25.7 2.2-34.9-6.9l-128-128z"/></svg>`,

        "spinner": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="animate-spin h-5" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M304 48a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zm0 416a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zM48 304a48 48 0 1 0 0-96 48 48 0 1 0 0 96zm464-48a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zM142.9 437A48 48 0 1 0 75 369.1 48 48 0 1 0 142.9 437zm0-294.2A48 48 0 1 0 75 75a48 48 0 1 0 67.9 67.9zM369.1 437A48 48 0 1 0 437 369.1 48 48 0 1 0 369.1 437z"/></svg>`
    },

    get shouldLockMagicButton() {
        return this.$store.abgrid.appIsRunning || this.$store.abgrid.appIsLocked;
    },

    magicButton: {

        [":class"]() {
            const isDisabled = this.shouldLockMagicButton
                ? "disabled"
                : ""
            return this.magicButtonMetaKeyIsPressed 
                ? `bg-red-700 border-red-700 ${this.magicButtonInitialClasses}`
                : `${isDisabled} ${customClasses} ${this.magicButtonInitialClasses}`
        },

        ["x-html"]() {
            return this.magicButtonAnimation
                ? this.magicButtonIcons["spinner"]
                : this.magicButtonMetaKeyIsPressed
                    ? this.magicButtonIcons["home"]
                    : label in this.magicButtonIcons
                        ? this.magicButtonIcons[label]
                        : label;
        },

        async ["@click"]({ metaKey }) {
            // Do nothing if ui is locked
            if (this.shouldLockMagicButton)
                return
            // overrid magic button action if meta key is pressed
            if (metaKey) {
                return this.navigateTo("/");
            }
            // Start magic button animation
            this.magicButtonAnimation = true;
            try {
                // Do magic button action
                await action.call(this);
            } finally {
                // Stop magic button animnation
                this.magicButtonAnimation = false;
            }
        },

        ["@keyup.shift.window"]() {
            this.magicButtonMetaKeyIsPressed = false;
        },

         ["@keydown.shift.window"]() {
            this.magicButtonMetaKeyIsPressed = true;
        },
    }
});