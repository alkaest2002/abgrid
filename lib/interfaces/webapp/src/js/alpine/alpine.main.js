/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import Alpine from "alpinejs";
import persist from "@alpinejs/persist";
import AlpineI18n from 'alpinejs-i18n';
import { appStore } from "./stores/app.store";
import { apiStore } from "./stores/api.store";
import { dataStore } from "./stores/data.store";
import componentOnline from "./components/component.online";
import componentNavigation from "./components/component.navigation";
import componentToast from "./components/component.toast";
import componentMagicButton from "./components/component.magic.button";
import componentApi from "./components/component.api";
import componentTextArea from "./components/component.textarea";
import componentDownloadManual from "./components/component.download.manual";
import viewHome from "./views/view.home";
import viewGroup from "./views/view.group";
import viewDropzoneEmpty from "./views/view.dropzone.empty";
import viewDropzoneData from "./views/view.dropzone.data";
import viewNotifyReport from "./views/view.notify.report";
import viewNotifyErrorYaml from "./views/view.notify.error.yaml";
import viewNotifyErrorApi from "./views/view.notify.error.api";
import viewNotifyQueue from "./views/view.notify.queue";
import viewMultistepSociogram from "./views/view.multistep.sociogram";
import viewMultistepData from "./views/view.multistep.data";
import i18nMessages from "./i18n/messages.json";

export const initAlpine = () => {
  Alpine.plugin(persist);
  Alpine.plugin(AlpineI18n);
  Alpine.store("app", appStore(Alpine));
  Alpine.store("api", apiStore(Alpine));
  Alpine.store("data", dataStore(Alpine));
  Alpine.data("componentApi", componentApi);
  Alpine.data("componentDownloadManual", componentDownloadManual);
  Alpine.data("componentMagicButton", componentMagicButton);
  Alpine.data("componentNavigation", componentNavigation);
  Alpine.data("componentOnline", componentOnline);
  Alpine.data("componentTextArea", componentTextArea);
  Alpine.data("componentToast", componentToast);
  Alpine.data("viewHome", viewHome);
  Alpine.data("viewGroup", viewGroup);
  Alpine.data("viewDropzoneEmpty", viewDropzoneEmpty);
  Alpine.data("viewDropzoneData", viewDropzoneData);
  Alpine.data("viewNotifyReport", viewNotifyReport);
  Alpine.data("viewNotifyErrorYaml", viewNotifyErrorYaml);
  Alpine.data("viewNotifyErrorApi", viewNotifyErrorApi);
  Alpine.data("viewNotifyQueue", viewNotifyQueue);
  Alpine.data("viewMultistepSociogram", viewMultistepSociogram);
  Alpine.data("viewMultistepData", viewMultistepData);
  Alpine.start();
  window.Alpine = Alpine;
  window.AlpineI18n.create("it", i18nMessages)
};
