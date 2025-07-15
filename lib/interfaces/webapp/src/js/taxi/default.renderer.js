import { Renderer } from "@unseenco/taxi";

export default class CustomRenderer extends Renderer {
  onEnterCompleted() {
     this.content?.classList && this.content.classList.remove("fade-in");
  }
}
