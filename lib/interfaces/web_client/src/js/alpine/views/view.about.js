import { add } from "../usables/use.stats.js";

export default () => ({
  check: {
    ["x-text"]() {
      return `view: about (${add(1, 3)})`;
    },
  },
});
