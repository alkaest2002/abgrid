export default () => ({

    async init() {

        // Unlock magic button
        this.$store.app.appMagicButtonIsLocked = false;

        // Poke server
        await this.apiPokeServer();

        // Poke server on online status changes
        this.$watch("$store.app.appIsOnline", async () => {
            await this.apiPokeServer();
        })

        // Preload pages
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.generate.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.dropzone.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.notify.html`);
    },

    serverStatusMessage: {
        ["x-html"]() {
            return this.$store.app.appIsOnline
                ? this.$store.api.apiServerIsReachable
                    ? `<span class='italic'>${this.$t('server.online')}</span> | <span class='italic'>${this.$t('server.up')}</span>`
                    : `<span class='italic'>${this.$t('server.online')}</span> | <span class='italic'>${this.$t('server.down')}</span>`
                : `<span class='italic'>${this.$t('server.offline')}</span> | <span class='italic'>${this.$t('server.down')}</span>`
            
        }
    },


    magicButton: {

        label: "next",

        async ["action"]() {
            
            // Refresh tocken if needed
            if (!this.$store.api.apiToken || this.$store.api.apiTokenNeedsToBeRefreshed) {
                
                // Create api request
                const apiRequest = {
                    endpoint: "api/token",
                    method: "GET",
                };
                
                // Make api request to server
                const apiResponse = await this.apiHandleRequest(apiRequest);
                
                // Save token and token timestamp to store
                this.$store.api.apiToken = apiResponse.data.detail;
                this.$store.api.apiTokenNeedsToBeRefreshed = false;
            }
            
            // Navigate to generate
            this.navigationGoTo("generate");
        }
    }
});
