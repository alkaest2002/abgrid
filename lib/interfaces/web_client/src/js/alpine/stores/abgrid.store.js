import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
  ["isLoginFlowRunning", false],
  ["isLogoutFlowRunning", false],
  ["isAuthenticated", false],
  ["token", ""],
  ["data", {}],
  ["reportHtml", ""],
  ["reportJson", {}],
];

const abgridStore = (Alpine) => ({
  ...initState(stateFn, Alpine, "_app"),

  wipeState(omit = ["isAuthenticated", "token"]) {
    wipeState.call(this, stateFn, omit);
  },
});

export { abgridStore };
