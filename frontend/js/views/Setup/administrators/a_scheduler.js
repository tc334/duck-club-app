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

const subroute = "hunts";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">scheduled auto actions</h1>
    <table id="data-table">
        <tr>
          <th>job id</th>
          <th>status</th>
          <th>hunt id</th>
          <th>commands</th>
        </tr>
      </table>
    `;
  }

  js(jwt) {
    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside(user_level);

    // First step is to pull data from DB
    const route = base_uri + "/" + subroute + "/scheduler";
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          console.log(response_full_json["data"]);
          populateTable(response_full_json["data"]);
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );
  }
}

function populateTable(db_data) {
  var table = document.getElementById("data-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["job_id"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["status"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["hunt_id"];

    var tabCell = tr.insertCell(-1);
    var str = "";
    for (var j = 0; j < db_data[i]["commands"].length; j++) {
      str += db_data[i]["commands"][j] + "\n";
    }
    tabCell.innerHTML = str;
  }
}
