export default () => ({
    
    async init() {},

    authButton: {
       
        "x-text"() { return "inizia sessione" },

        async "@click"() {
            try {
                const res = await fetch(this.$store.abgrid.apiTokenEndpoint);
                const token = await res.json();
                this.$store.abgrid.token = token
            } catch (error) {
                window.TaxinavigateTo("/pages/it.contact.html")
            }
        },
    }
});
