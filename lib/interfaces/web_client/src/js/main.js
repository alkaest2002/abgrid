import { createAuth0Client } from '@auth0/auth0-spa-js';
import { initAlpine } from "./alpine/alpine.main";
import { initTaxi } from "./taxi/taxi.main";

createAuth0Client({
    domain: "alkaest2002.eu.auth0.com",
    clientId: "XRKutHPS1ovEdV3LMgJYKLlBfgUQv8Df",
    authorizationParams: { redirect_uri: window.location.origin }
}).then(auth0Client => {
    // Attach auth0 client to window
    window.Auth0Client = auth0Client;
    // Init alpine
    initAlpine();
    // Init taxi
    initTaxi();
});

