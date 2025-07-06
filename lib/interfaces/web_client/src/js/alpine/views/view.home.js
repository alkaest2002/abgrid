export default () => ({

    magicButton: {

        label: "next",

        async ["action"]() {
            this.$store.abgrid.apiRequest = {
                endpoint: "api/token",
                method: "GET",
            };
        }
    }
});
