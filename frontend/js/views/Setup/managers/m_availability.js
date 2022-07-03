import AbstractView from "../../AbstractView.js";
import { base_uri } from "../../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside,
  decode_jwt,
} from "../../../common_funcs.js";

var jwt_global;
var db_data;
const subroute = "ponds";
const singular = "pond";
const plural = "ponds";
var list_of_changes = [];

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return (
      `<div class="reload-message"></div>
    <h1 class="heading-primary">ponds</h1>
    <table id="` +
      singular +
      `-table">
      <tr>
        <th>id</th>
        <th>name</th>
        <th>status</th>
      </tr>
    </table>
    <button class="btn--form" id="btn-pond-status-update">Update</button>`
    );
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
    const route = base_uri + "/pond_status";
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json[subroute]) {
          db_data = response_full_json[subroute];
          populateTable(db_data);
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    var updateButton = document.getElementById("btn-pond-status-update");
    updateButton.addEventListener("click", () => {
      if (list_of_changes.length == 0) {
        displayMessageToUser("No changes to submit");
      } else {
        var json = [];
        for (var i = 0; i < list_of_changes.length; i++) {
          // default closed. check for open
          var current_status = "closed";
          const id_str = "inp-pond-open" + "-" + list_of_changes[i];
          const radioButton_open = document.getElementById(id_str);
          if (radioButton_open.checked) {
            current_status = "open";
          }

          json.push({
            id: db_data[list_of_changes[i]]["id"],
            status: current_status,
          });
        }

        const route_put = base_uri + "/ponds";
        // now send the changes to the DB
        callAPI(
          jwt,
          route_put,
          "PUT",
          JSON.stringify(json),
          (data) => {
            localStorage.setItem("previous_action_message", data["message"]);
            window.scrollTo(0, 0);
            location.reload();
          },
          displayMessageToUser
        );
      }
    });

    // What do do on a submit
    /* myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));

      // for ponds, we need to extract the property["id"] from what we currently have, which is the property["name"]
      const searchResult = db_data_properties.filter(function (property) {
        return property["name"] === object["property_id"];
      })[0]["id"];
      object["property_id"] = searchResult;

      // now we can stringify the json just like we do on the other views
      var json = JSON.stringify(object);

      if (e.submitter.id == "btn-add") {
        const route = base_uri + "/" + subroute;

        callAPI(
          jwt,
          route,
          "POST",
          json,
          (data) => {
            localStorage.setItem("previous_action_message", data["message"]);
            window.scrollTo(0, 0);
            location.reload();
          },
          displayMessageToUser
        );
      } else if (e.submitter.id == "btn-update") {
        // attach the primary key (id) to the json & send at PUT instead of POST
        const route =
          base_uri +
          "/" +
          subroute +
          "/" +
          document.getElementById(singular + "-id").value;

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
      }
    }); */
  }
}

function populateTable(db_data) {
  var table = document.getElementById(singular + "-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["id"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["name"];

    var tabCell = tr.insertCell(-1);
    var label_open = document.createElement("label");
    label_open.for = "inp-pond-open" + "-" + i;
    label_open.innerHTML = "open";
    label_open.className += "lbl-pond-status";
    var input_open = document.createElement("input");
    input_open.type = "radio";
    input_open.id = "inp-pond-open" + "-" + i;
    input_open.value = "open";
    input_open.name = "pond-availability" + "-" + i;
    input_open.className += "inp-pond-open";
    input_open.row_idx = i;
    input_open.addEventListener("change", radioChange);
    var label_closed = document.createElement("label");
    label_closed.for = "inp-pond-closed" + "-" + i;
    label_closed.innerHTML = "closed";
    label_closed.className += "lbl-pond-status";
    var input_closed = document.createElement("input");
    input_closed.type = "radio";
    input_closed.id = "inp-pond-closed" + "-" + i;
    input_closed.value = "closed";
    input_closed.name = "pond-availability" + "-" + i;
    input_closed.className += "inp-pond-open";
    input_closed.row_idx = i;
    input_closed.addEventListener("change", radioChange);

    if (db_data[i]["status"] == "open") {
      input_open.checked = "checked";
    } else {
      input_closed.checked = "checked";
    }

    tabCell.appendChild(input_open);
    tabCell.appendChild(label_open);
    tabCell.appendChild(input_closed);
    tabCell.appendChild(label_closed);
  }
}

function radioChange(e) {
  // this will indicate to the update button to include this row in the PUT call
  if (!list_of_changes.includes(e.currentTarget.row_idx)) {
    list_of_changes.push(e.currentTarget.row_idx);
  }
}
