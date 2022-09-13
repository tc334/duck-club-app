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
var db_data_hunt;
const subroute = "users";
const singular = "user";
const plural = "users";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">Manually Remove Hunters</h1>
    <div class="hunter-list">
      <span>active hunters:</span>
      <select id="select-hunter"></select>
    </div>
    <div id="hunt-identifier"></div>
    <button class="btn--form" id="btn-remove">Remove</button>
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

    // First step is to pull data from DB
    const route = base_uri + "/groupings/current_users";
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          db_data = response_full_json["data"];
          //console.log(db_data);
          populateHunterListBox();
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // What do do on a submit
    document.getElementById("btn-remove").addEventListener("click", () => {
      // Pull currently selected user from select
      const idxHunter = document.getElementById("select-hunter").value;

      const route =
        base_uri +
        "/groupings/remove/" +
        db_data[idxHunter]["group_id"] +
        "/" +
        db_data[idxHunter]["slot_num"];

      var json = JSON.stringify({ dummy: 0 });

      callAPI(
        jwt,
        route,
        "PUT",
        json,
        (data) => {
          localStorage.setItem("previous_action_message", data["message"]);
          window.scrollTo(0, 0);
          location.reload();
        },
        displayMessageToUser
      );
    });
  }
}

function populateHunterListBox() {
  var select = document.getElementById("select-hunter");
  for (var i = 0; i < db_data.length; i++) {
    var option_new = document.createElement("option");
    option_new.value = i;
    option_new.innerHTML =
      db_data[i]["first_name"] + " " + db_data[i]["last_name"];
    select.appendChild(option_new);
  }
}
