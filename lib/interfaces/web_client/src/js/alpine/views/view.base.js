export default () => ({

    magicButton: {

        label: "inizia sessione",

        async ["action"]() {
            try {
                // Init api request
                this.$store.abgrid.apiRequestIsRunning = true;
                // Start api request
                const res = await fetch(this.$store.abgrid.apiTokenEndpoint);
                // Get api data as json
                const { detail } = await res.json();
                // Store api data
                this.$store.abgrid.apiData = detail;
                // On non 200 status
                if (!res.ok) {
                    // Go to notification page
                    return this.$store.abgrid.navigateTo("notify");
                }
                // Save token
                this.$store.abgrid.apiToken = detail;
                // Go to switcher page
                this.$store.abgrid.navigateTo("switcher");

            // server error
            } catch (error) {
                // Reset apiData
                this.$store.abgrid.apiData = {};
                // Reset token
                this.$store.abgrid.apiToken = "";
                // Go to notification page
                this.$store.abgrid.navigateTo("notify");
            } finally {
                // End api request
                this.$store.abgrid.apiRequestIsRunning = false;
            }
        }
    }
});
