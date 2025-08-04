/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
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
            return this.$store.api.apiServerIsReachable
                ? `<span class='italic'>${this.$t('server.up')}</span>`
                : `<span class='italic'>${this.$t('server.down')}</span>`
        }
    },

    apiTokenKey: {
        ["x-model.trim"]: "$store.api.apiToken",

        ["@click"]() {
            this.$el.select();
        },

        ["@focus"]() {
            this.$el.classList.toggle("text-black")
            this.$el.classList.toggle("text-gray-400")
        },

        ["@blur"]() {
            this.$el.classList.toggle("text-black")
            this.$el.classList.toggle("text-gray-400")
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
