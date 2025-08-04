/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { Renderer } from "@unseenco/taxi";

export default class CustomRenderer extends Renderer {
  onEnterCompleted() {
     this.content?.classList && this.content.classList.remove("fade-in");
  }
}
