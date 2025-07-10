import Alpine from "alpinejs";
import AsyncAlpine from "async-alpine";
import persist from "@alpinejs/persist";
import AlpineI18n from 'alpinejs-i18n';
import { abgridStore } from "./stores/abgrid.store";
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
  Alpine.store("abgrid", abgridStore(Alpine));
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
