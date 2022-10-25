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
    <button class="btn--form" id="btn-force-recount">Force Harvest Recount</button>
    <br>
    <button class="btn--form" id="btn-hunter-recount">Force Hunter Recount (all, which is SLOW!)</button>
    <br>
    <button class="btn--form" id="btn-hunter-recount-onehunt">Force Hunter Recount (one hunt)</button>
    <br>
    <button class="btn--form" id="btn-cache-flush">Flush Cache</button>
    <br>
    <button class="btn--form" id="btn-deselect-all-ponds">Set All Ponds to Not Selected</button>
    <br>
    <button class="btn--form" id="btn-clear-queue">Clear RQ Queue</button>
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

    const route5 = base_uri + "/stats/force_hunter_recount";

    document
      .getElementById("btn-hunter-recount")
      .addEventListener("click", () => {
        callAPI(
          jwt,
          route5,
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

    const route55 = base_uri + "/stats/force_hunter_recount";

    document
      .getElementById("btn-hunter-recount-onehunt")
      .addEventListener("click", () => {
        let hunt_id = prompt("What hunt id do you want to recount?");
        if (hunt_id != null) {
          callAPI(
            jwt,
            route55 + "/" + hunt_id,
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
        }
      });

    const route2 = base_uri + "/stats/flush_cache";

    document.getElementById("btn-cache-flush").addEventListener("click", () => {
      callAPI(
        jwt,
        route2,
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

    document
      .getElementById("btn-deselect-all-ponds")
      .addEventListener("click", () => {
        const route3 = base_uri + "/ponds/reset_selections";

        callAPI(
          jwt,
          route3,
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

    const route3 = base_uri + "/hunts/clear_rq";

    document.getElementById("btn-clear-queue").addEventListener("click", () => {
      callAPI(
        jwt,
        route3,
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
