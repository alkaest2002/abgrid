/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["apiServerIsReachable", true],
    ["apiRequestIsPending", false],
    ["apiToken", ""],
    ["apiRequest", {}],
    ["apiResponse", {}],
];

const abgridApiStore = (Alpine) => ({

    ...initState(stateFn, Alpine, "_api"),

    get apiTokenIsStructurallyValid() {
        return this.apiTokenExpirationDate instanceof Date;
    },

    get apiTokenExpirationDate() {
        if (!this.apiToken) return null;
        try {
            // Split candidate JWT token into parts (header.payload.signature)
            const parts = this.apiToken.split(".");
            // Throw error if JWT is malformed
            if (parts.length !== 3) throw new Error("invalid_jwt_token");
            // Decode the payload (second part) and extract exp claim
            const { exp } = JSON.parse(atob(parts[1]));
            // Throw error if exp claim is missing
            if (!exp) throw new Error("invalid_jwt_token");
            // Convert exp to Date object and return it
            return new Date(exp * 1000);
        } catch (error) {
            return null;
        }
    },

    get apiTokenExpirationDateFormatted() {
        if (!this.apiTokenExpirationDate) return null;
        try {
            const language = Alpine.store("app").appLanguage;
            return this.apiTokenExpirationDate.toLocaleDateString(language);
        } catch (error) {
            return this.apiTokenExpirationDate.toLocaleDateString("en");
        }
    },

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});

export { abgridApiStore };
