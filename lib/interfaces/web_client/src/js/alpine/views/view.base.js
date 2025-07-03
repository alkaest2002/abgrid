export default () => ({

    authButton: {

        "x-text"() { return "inizia sessione" },

        async "@click"() {
            try {

                // Init api request
                this.$store.abgrid.apiRequestIsRunning = true;
                // Perform request
                const res = await fetch(this.$store.abgrid.apiTokenEndpoint);
                // Get api data as json
                const { detail } = await res.json();
                // Store api data
                this.$store.abgrid.apiData = detail;
                // On non 200 status
                if (!res.ok) {
                    // Go to notification page
                    return window.Taxi.navigateTo("/pages/it.notify.html");
                }
                // Save token
                this.$store.abgrid.apiToken = detail;
                // Go to switcher page
                window.Taxi.navigateTo("/pages/it.switcher.html");

            // server error
            } catch (error) {
                // Reset apiData and token
                this.$store.abgrid.apiData = {};
                this.$store.abgrid.apiToken = "";
                // Go to notification page
                window.Taxi.navigateTo("/pages/it.notify.html");
            } finally {
                // End api request
                this.$store.abgrid.apiRequestIsRunning = false;
            }
        }
    }
});
