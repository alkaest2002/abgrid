export default () => ({

    magicButton: {

        label: "next",

        async ["action"]() {
            // Store api request 
            this.$store.abgrid.apiRequest = {
                endpoint: "api/token",
                method: "GET",
            };
            // Call server
            await this.apiHandleRequest(this.$store.abgrid.apiRequest);
            // Save token in store
            this.$store.abgrid.apiToken = this.$store.abgrid.apiResponse.data.detail;
            // Navigate to generate
            this.navigationGoTo("generate");
        }
    }
});
