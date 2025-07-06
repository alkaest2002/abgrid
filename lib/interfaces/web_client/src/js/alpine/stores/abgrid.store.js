import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
  ["appIsOnline", true],
  ["appIsLocked", false],
  ["appIsRunning", false],
  ["appLanguage", "it"],
  ["appResponse", {}],
  ["apiToken", ""],
  ["apiRequest", {}],
  ["apiResponse", {}],
];

const abgridStore = (Alpine) => ({
  ...initState(stateFn, Alpine, "_app"),

  get apiBase() {
    return import.meta.env.DEV
      ? "http://localhost:7895"
      : "https://abgrid.onrender.com"
  },

  apiEndpoint(command) {
    return `${this.apiBase}/api/${command}`
  },

  wipeState(omit = []) {
    wipeState.call(this, stateFn, omit);
  },
});

export { abgridStore };
