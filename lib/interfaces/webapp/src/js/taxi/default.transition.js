import { Transition } from "@unseenco/taxi";

export default class MyTransition extends Transition {
  /**
   * handle the transition leaving the previous page
   * @param { { from: HTMLElement, trigger: string|HTMLElement|false, done: function } } props
   */
  onLeave({ from, done }) {
    from.removeEventListener("animationend", done);
    done();
  }

  /**
   * handle the transition entering the next page
   * @param { { to: HTMLElement, trigger: string|HTMLElement|false, done: function } } props
   */
  onEnter({ to, done }) {
    to.classList.add("fade-in");
    to.addEventListener("animationend", done);
  }
}
