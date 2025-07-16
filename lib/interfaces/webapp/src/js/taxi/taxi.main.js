import { Core } from "@unseenco/taxi";
import defaultRenderer from "./default.renderer.js";
import defaultTransition from "./default.transition.js";

export const initTaxi = () => {
  window.Taxi = new Core({
    bypassCache: true,
    allowInterruption: true,
    renderers: { default: defaultRenderer },
    transitions: { default: defaultTransition },
  });
};