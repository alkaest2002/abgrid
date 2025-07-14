import Alpine from "alpinejs";
import AsyncAlpine from "async-alpine";
import persist from "@alpinejs/persist";
import AlpineI18n from 'alpinejs-i18n';
import { abgridAppStore } from "./stores/abgrid.app.store";
import { abgridApiStore } from "./stores/abgrid.api.store";
import { abgridDataStore } from "./stores/abgrid.data.store";
import componentOnline from "./components/component.online";
import componentNavigation from "./components/component.navigation";
import componentToast from "./components/component.toast";
import componentMagicButton from "./components/component.magic.button";
import componentApi from "./components/component.api";
import componentTextArea from "./components/component.textarea";
import viewHome from "./views/view.home";
import viewNotify from "./views/view.notify";
import i18nMessages from "./i18n/messages.json";

export const initAlpine = () => {
  Alpine.plugin(persist);
  Alpine.plugin(AsyncAlpine);
  Alpine.plugin(AlpineI18n);
  Alpine.store("app", abgridAppStore(Alpine));
  Alpine.store("api", abgridApiStore(Alpine));
  Alpine.store("data", abgridDataStore(Alpine));
  Alpine.data("componentToast", componentToast);
  Alpine.data("componentMagicButton", componentMagicButton);
  Alpine.data("componentOnline", componentOnline);
  Alpine.data("componentNavigation", componentNavigation);
  Alpine.data("componentApi", componentApi);
  Alpine.data("componentTextArea", componentTextArea);
  Alpine.data("viewHome", viewHome);
  Alpine.data("viewNotify", viewNotify);
  Alpine.asyncData("viewGenerate", () => import("./views/view.generate"));
  Alpine.asyncData("viewDropzone", () => import("./views/view.dropzone"));
  Alpine.start();
  window.Alpine = Alpine;
  window.AlpineI18n.create("it", i18nMessages)
};
