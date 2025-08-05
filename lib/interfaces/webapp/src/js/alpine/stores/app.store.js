/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["appIsOnline", true],
    ["appIsElectron", "electronAPI" in window],
    ["appLanguage", "it"],
    ["appMagicButtonIsLocked", false],
];

export const appStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_app"),

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});