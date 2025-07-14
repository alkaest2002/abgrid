import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["apiToken", ""],
    ["apiTokenTimestamp", null],
    ["apiRequestIsPending", false],
    ["apiRequest", {}],
    ["apiResponse", {}],
];

const abgridApiStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_api"),

    wipeState(resetProps = null) {
        wipeState.call(this, stateFn, resetProps);
    },
});

export { abgridApiStore };
