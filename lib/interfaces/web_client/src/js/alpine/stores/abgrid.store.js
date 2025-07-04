import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
  ["language", "it"],
  ["contextIsDevelopment", true],
  ["apiRequestIsRunning", false],
  ["apiEndpointDev", "http://localhost:7895"],
  ["apiEndpointProd", "https://abgrid.onrender.com"],
  ["notify", ""],
  ["apiData", {}],
  ["apiToken", ""],
];

const abgridStore = (Alpine) => ({
  ...initState(stateFn, Alpine, "_app"),

  get apiTokenEndpoint() {
    return this.contextIsDevelopment
      ? `${this.apiEndpointDev}/api/token`
      : `${this.apiEndpointProd}/api/token`
  },

  get apiReportEndpoint() {
    return this.contextIsDevelopment
      ? `${this.apiEndpointDev}/api/report`
      : `${this.apiEndpointProd}/api/report`
  },

  wipeState(omit = []) {
    wipeState.call(this, stateFn, omit);
  },
});

export { abgridStore };
