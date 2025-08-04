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
            // Navigate to group page
            this.navigationGoTo("group");
        }
    }
});
