import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["appIsOnline", true],
    ["appLanguage", "it"],
    ["appMagicButtonIsLocked", false],
];

const abgridAppStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_app"),

    wipeState(resetProps = null) {
        wipeState.call(this, stateFn, resetProps);
    },
});

export { abgridAppStore };
