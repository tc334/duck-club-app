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
    <div id="foo"></div>
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
          //console.log(response_full_json["data"]);
          var my_div = document.getElementById("foo");
          my_div.innerHTML = response_full_json["data"];
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
    tabCell.innerHTML = db_data[i]["id"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = dateConverter_http(db_data[i]["hunt_date"], true);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["status"];

    // auto close signup
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["signup_closed_auto"];

    // signup close time
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["signup_closed_time"];

    // auto draw
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["draw_method_auto"];

    // auto open hunt
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["hunt_open_auto"];

    // hunt open time
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["hunt_open_time"];

    // auto close hunt
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["hunt_close_auto"];

    // hunt close time
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["hunt_closed_time"];

    var tabCell = tr.insertCell(-1);

    // Edit button
    var btn_edt = document.createElement("button");
    btn_edt.index = i;
    btn_edt.innerHTML = "Edit";
    btn_edt.className += "btn--action";
    btn_edt.addEventListener("click", populateEdit);
    tabCell.appendChild(btn_edt);
    // Slash
    tabCell.insertAdjacentText("beforeend", "\x2F");
    // Delete button
    var btn_del = document.createElement("button");
    btn_del.my_id = db_data[i]["id"];
    btn_del.innerHTML = "Del";
    btn_del.className += "btn--action";
    btn_del.addEventListener("click", delMember);
    tabCell.appendChild(btn_del);
  }
}
