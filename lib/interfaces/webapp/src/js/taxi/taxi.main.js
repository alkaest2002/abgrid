/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { Core } from "@unseenco/taxi";
import defaultRenderer from "./default.renderer.js";
import defaultTransition from "./default.transition.js";

export const initTaxi = () => {
  window.Taxi = new Core({
    bypassCache: false,
    allowInterruption: true,
    renderers: { default: defaultRenderer },
    transitions: { default: defaultTransition },
  });
};