export default () => ({

    check: {
        ["x-text"]() {
            return "view: index";
        },
    },

    vButton: {
        "x-text"() { return "prova" },

        "@click"() { 
            window.Auth0Client.loginWithRedirect() 
        },
    }
});
