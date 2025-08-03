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

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});

export { abgridApiStore };
