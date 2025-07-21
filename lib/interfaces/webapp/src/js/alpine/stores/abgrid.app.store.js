import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["appIsOnline", true],
    ["appIsElectron", "electronAPI" in window],
    ["appLanguage", "it"],
    ["appMagicButtonIsLocked", false],
];

const abgridAppStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_app"),

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});

export { abgridAppStore };
