import AbstractView from "../../AbstractView.js";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">Logout</h1>
    `;
  }

  js(jwt) {
    localStorage.removeItem("token");
    console.log("JWT deleted");
    location.href = "login.html";
  }
}
