/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["apiServerIsReachable", true],
    ["apiRequestIsPending", false],
    ["apiToken", ""],
    ["apiTokenIsValid", true],
    ["apiRequest", {}],
    ["apiResponse", {}],
];

const abgridApiStore = (Alpine) => ({

    ...initState(stateFn, Alpine, "_api"),

    get apiTokenExpirationDate() {
        try {
            // Split JWT token into parts (header.payload.signature)
            const parts = this.apiToken.split(".");
            if (parts.length !== 3) throw new Error("invalid_jwt_token");
            // Decode the payload (second part)
            const payload = JSON.parse(atob(parts[1]));
            // Extract exp claim and convert to Date object
            if (!payload.exp) throw new Error("invalid_jwt_token");
            this.apiTokenIsValid = true;
            return new Date(payload.exp * 1000).toLocaleDateString("it-IT", {
                year: "2-digit",
                month: "2-digit",
                day: "2-digit"
            });
        } catch (error) {
            this.apiTokenIsValid = false;
            return null;
        }
    },

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});

export { abgridApiStore };
