import AbstractView from "../../AbstractView.js";
import { base_uri } from "../../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside,
  dateConverter_http,
  decode_jwt,
} from "../../../common_funcs.js";

var jwt_global;
var db_data;
const subroute = "hunts";
const singular = "hunt";
const plural = "hunts";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">Miscellaneous</h1>
    <button class="btn--form" id="btn-force-recount">Force Recount</button>
    `;
  }

  js(jwt) {
    // this variable is copied into the higher namespace so I can get it
    // into the delete function
    jwt_global = jwt;

    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside(user_level);

    const route = base_uri + "/stats/force_recount";

    document
      .getElementById("btn-force-recount")
      .addEventListener("click", () => {
        callAPI(
          jwt,
          route,
          "GET",
          null,
          (response_full_json) => {
            if (response_full_json["message"]) {
              displayMessageToUser(response_full_json["message"]);
            } else {
              //console.log(data);
            }
          },
          displayMessageToUser
        );
      });
  }
}
