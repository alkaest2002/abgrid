export default (label, action, customClasses = "bg-blue-700 border-blue-700") => ({

    animation: false,

    icons: {
        
        "next": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-5" viewBox="0 0 256 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M246.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-9.2-9.2-22.9-11.9-34.9-6.9s-19.8 16.6-19.8 29.6l0 256c0 12.9 7.8 24.6 19.8 29.6s25.7 2.2 34.9-6.9l128-128z"/></svg>`,

        "prev": `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="h-5" viewBox="0 0 256 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M9.4 278.6c-12.5-12.5-12.5-32.8 0-45.3l128-128c9.2-9.2 22.9-11.9 34.9-6.9s19.8 16.6 19.8 29.6l0 256c0 12.9-7.8 24.6-19.8 29.6s-25.7 2.2-34.9-6.9l-128-128z"/></svg>`
    },

    initialClasses: "h-12 w-12 rounded-full text-sm font-medium text-white border shadow-sm inline-flex justify-center items-center cursor-pointer",

    get animationClasses() {
        return this.animation ? "animate-spin" : "";
    },

    get buttonClasses() {
        return `${customClasses} ${this.initialClasses}`
    },

    ["buttonLabel"]() {

        return this.animation 
            ? `<svg xmlns="http://www.w3.org/2000/svg" fill="#fff" class="${this.animationClasses} h-5" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M304 48a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zm0 416a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zM48 304a48 48 0 1 0 0-96 48 48 0 1 0 0 96zm464-48a48 48 0 1 0 -96 0 48 48 0 1 0 96 0zM142.9 437A48 48 0 1 0 75 369.1 48 48 0 1 0 142.9 437zm0-294.2A48 48 0 1 0 75 75a48 48 0 1 0 67.9 67.9zM369.1 437A48 48 0 1 0 437 369.1 48 48 0 1 0 369.1 437z"/></svg>`
            : label in this.icons
                ? this.icons[label]
                : label
    },

    async ["buttonAction"]({ metaKey }) {
        if (metaKey) {
            return this.navigateTo("/");
        }
        this.animation = true;
        try {
            await action.call(this);
        } finally {
            this.animation = false;
        }
    },
});