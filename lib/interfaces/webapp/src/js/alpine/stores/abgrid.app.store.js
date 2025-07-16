import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["appIsOnline", true],
    ["appLanguage", "it"],
    ["appMagicButtonIsLocked", false],
    ["appIsElectron", "electronAPI" in window]
];

const abgridAppStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_app"),

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});

export { abgridAppStore };
