/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["apiServerIsReachable", true],
    ["apiRequestIsPending", false],
    ["apiToken", ""],
    ["apiTokenIsStructurallyValid", true],
    ["apiRequest", {}],
    ["apiResponse", {}],
];

const abgridApiStore = (Alpine) => ({

    ...initState(stateFn, Alpine, "_api"),

    get apiTokenExpirationDate() {
        try {
            // Get current app language
            const language = Alpine.store("app").appLanguage;
            // Split candidate JWT token into parts (header.payload.signature)
            const parts = this.apiToken.split(".");
            // Throw error is JWT is malformed
            if (parts.length !== 3) throw new Error("invalid_jwt_token");
            // Decode the payload (second part) and extract exp claim
            const { exp } = JSON.parse(atob(parts[1]));
            // Throw error if exp claim is missing
            if (!exp) throw new Error("invalid_jwt_token");
            // JWT is structurally valid
            this.apiTokenIsStructurallyValid = true;
            // Convert exp to Date object
            const expirationDate = new Date(exp * 1000);
            // return expirationDate as locale string
            return expirationDate
                .toLocaleDateString(language, {
                    year: "2-digit",
                    month: "2-digit",
                    day: "2-digit"
                }
            );
        } catch (error) {
            this.apiTokenIsStructurallyValid = false;
            return null;
        }
    },

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});

export { abgridApiStore };
