export default () => ({

    async init() {

        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
        
        // Poke server
        await this.apiPokeServer();

        // Poke server on online status changes
        this.$watch("$store.app.appIsOnline", async () => {
            await this.apiPokeServer();
        })

        // Preload pages
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.group.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.dropzone.empty.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.dropzone.data.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.notify.report.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.notify.error.yaml.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.notify.error.api.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.notify.queue.html`);
    },

    serverStatusMessage: {
        ["x-html"]() {
            return this.$store.app.appIsOnline
                ? this.$store.api.apiServerIsReachable
                    ? `<span class='italic'>${this.$t('server.online')}</span> | <span class='italic'>${this.$t('server.up')}</span>`
                    : `<span class='italic'>${this.$t('server.online')}</span> | <span class='italic'>${this.$t('server.down')}</span>`
                : this.$store.api.apiServerIsReachable 
                    ? `<span class='italic'>${this.$t('server.offline')}</span> | <span class='italic'>${this.$t('server.up')}</span>`
                    : `<span class='italic'>${this.$t('server.offline')}</span> | <span class='italic'>${this.$t('server.down')}</span>`
        }
    },


    magicButton: {

        label: "next",

        async ["action"]() {
            
            // Refresh tocken if needed
            if (!this.$store.api.apiToken || this.$store.api.apiTokenIsInvalid) {
                
                // Create api request
                const apiRequest = {
                    endpoint: "api/token",
                    method: "GET",
                };
                
                // Make api request to server
                const { statusCode, data: { detail: apiToken = null }} = await this.apiHandleRequest(apiRequest);
                
                // On api success
                if (statusCode == 200) {
                    // Save token and invalid token flag to store
                    this.$store.api.apiToken = apiToken;
                    this.$store.api.apiTokenIsInvalid = false;
                    // Navigate to group page
                    this.navigationGoTo("group");
                // On api queue error
                } else if (statusCode == 429) {
                    // Navigate to queue notification page
                    this.navigationGoTo("notify.queue");
                // On any other api error
                } else {
                    // Navigate to error api notification page
                    this.navigationGoTo("notify.error.api");
                }
            }
        }
    }
});
