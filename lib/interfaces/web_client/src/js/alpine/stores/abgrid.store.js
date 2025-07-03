import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
  ["devEndpoint", "http://localhost:7895"],
  ["prodEndpoint", "https://abgrid.onrender.com"],
  ["isDev", true],
  ["token", ""],
  ["data", {}],
  ["reportHtml", ""],
  ["reportJson", {}],
];

const abgridStore = (Alpine) => ({
  ...initState(stateFn, Alpine, "_app"),

  get apiTokenEndpoint() {
    return this.isDev
      ? `${this.devEndpoint}/api/token`
      : `${this.prodEndpoint}/api/token`
  },

  get apiReportEndpoint() {
    return this.isDev
      ? `${this.devEndpoint}/api/report`
      : `${this.prodEndpoint}/api/report`
  },

  wipeState(omit = []) {
    wipeState.call(this, stateFn, omit);
  },
});

export { abgridStore };
