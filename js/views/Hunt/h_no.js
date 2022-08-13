import AbstractView from "../AbstractView.js";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">No active hunts &#9785;</h1>`;
  }

  js(jwt) {
    // clear the aside
    var aside = document.getElementById("aside-content");
    aside.innerHTML = "";
  }
}
