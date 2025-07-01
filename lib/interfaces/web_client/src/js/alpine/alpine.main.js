import Alpine from "alpinejs";
import AsyncAlpine from "async-alpine";
import persist from "@alpinejs/persist";
import { abgridStore } from "./stores/abgrid.store";
import viewBase from "./views/view.base";

export const initAlpine = () => {
  Alpine.plugin(persist);
  Alpine.plugin(AsyncAlpine);
  Alpine.store("abgrid", abgridStore);
  Alpine.data("viewBase", viewBase);
  Alpine.asyncData("viewAbout", () => import("./views/view.about"));
  Alpine.start();
  window.Alpine = Alpine;
  console.log(Alpine)
};
