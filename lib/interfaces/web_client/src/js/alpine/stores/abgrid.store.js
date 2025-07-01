import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
  ["title", "abgrid-store"],
  ["gdpr", false],
];

const abgridStore = (Alpine) => ({
  ...initState(stateFn, Alpine, "_app"),

  wipeState(omit = []) {
    wipeState.call(this, stateFn, omit);
  },
});

export { abgridStore };
