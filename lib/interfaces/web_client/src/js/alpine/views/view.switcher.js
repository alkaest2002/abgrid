export default () => ({

    magicButton: {

        label: "home",

        ["action"]() {
            this.$store.abgrid.navigateTo("/");
        }
    }
});
