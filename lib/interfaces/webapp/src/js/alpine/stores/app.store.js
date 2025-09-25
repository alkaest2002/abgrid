/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { initState, wipeState } from "../usables/use.alpine.store.js";

// Check if running in Electron
const appIsElectron = !!window.electronAPI

// Check if function exists and call it, otherwise return null
const appElectronVersion = (typeof window.electronAPI?.getElectronVersion === "function") 
    ? await window.electronAPI.getElectronVersion().catch(() => null)
    : null;

const stateFn = () => [
    ["appIsElectron", appIsElectron],
    ["appElectronVersion", appElectronVersion || null, false],
    ["appIsOnline", true],
    ["appLanguage", "it"],
    ["appMagicButtonIsLocked", false],
];

export const appStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_app"),

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});