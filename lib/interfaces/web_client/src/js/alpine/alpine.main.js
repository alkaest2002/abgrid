import Alpine from "alpinejs";
import AsyncAlpine from "async-alpine";
import persist from "@alpinejs/persist";
import { abgridStore } from "./stores/abgrid.store";
import componentOnline from "./components/component.online";
import componentNavigation from "./components/component.navigation";
import componentButton from "./components/component.button";
import viewBase from "./views/view.base";
import viewNotify from "./views/view.notify";

export const initAlpine = () => {
  Alpine.plugin(persist);
  Alpine.plugin(AsyncAlpine);
  Alpine.store("abgrid", abgridStore(Alpine));
  Alpine.data("componentOnline", componentOnline);
  Alpine.data("componentNavigation", componentNavigation);
  Alpine.data("componentButton", componentButton);
  Alpine.data("viewBase", viewBase);
  Alpine.data("viewNotify", viewNotify);
  Alpine.asyncData("viewSwitcher", () => import("./views/view.switcher"));
  Alpine.asyncData("viewGroup", () => import("./views/view.group"));
  Alpine.asyncData("viewReport", () => import("./views/view.report"));
  Alpine.start();
  window.Alpine = Alpine;
};
