export default () => ({

    magicButton: {

        label: "next",

        ["action"]() {
            // Handle metakey
            if (this.magicButtonMetaKeyIsPressed)
                return this.navigateTo("/");
            this.navigateTo("notify");
        }
    }
});
