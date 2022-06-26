import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside,
  dateConverter,
  decode_jwt,
} from "../common_funcs.js";

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
    return (
      `<div class="reload-message"></div>
    <h1 class="heading-primary">hunts</h1>
    <table id="data-table">
      <tr>
        <th>id</th>
        <th>date</th>
        <th>status</th>
        <th>auto CS</th>
        <th>SC time</th>
        <th>auto draw</th>
        <th>auto OH</th>
        <th>HO time</th>
        <th>auto CH</th>
        <th>hunt CT</th>
        <th>actions</th>
      </tr>
    </table>

    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">add/edit ` +
      singular +
      `</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <label for="` +
      singular +
      `-id">Hunt ID</label>
        <input id="` +
      singular +
      `-id" type="text" placeholder="n/a" name="id" disabled />
    
        <label for="inp-hunt-date">hunt date</label>
        <input
          id="inp-hunt-date"
          type="date"
          name="hunt_date"
          required
        />

        <label for="select-status">Status</label>
        <select id="select-status" name="status" required>
          <option value="signup_open">signup open</option>
          <option value="signup_closed">signup closed</option>
          <option value="draw_complete">draw complete</option>
          <option value="hunt_open">hunt open</option>
          <option value="hunt_closed">hunt closed</option>
        </select>

        <span class="button-holder">
          <button class="btn--form">Add</button>
          <button class="btn--form" id="btn-update" disabled>Update</button>
          <input class="btn--form" type="reset" />
        </span>
      </div>
    </form>`
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
    const route = base_uri + "/" + subroute;
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

    // When the "reset" button is hit, only "add" should be enabled
    // "update" will get enabled if a user hits an "edit" in the main table
    const myForm = document.getElementById("add-edit-form");
    myForm.addEventListener("reset", function (e) {
      document.getElementById("btn-add").disabled = false;
      document.getElementById("btn-update").disabled = true;
      setDefaultDate();
    });

    // What do do on a submit
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));

      // checkboxes require special handling
      const checkbox_names = [
        "hunt_close_auto",
        "hunt_open_auto",
        "signup_closed_auto",
      ];
      for (var i = 0; i < checkbox_names.length; i++) {
        if (object[checkbox_names[i]] && object[checkbox_names[i]] == "on") {
          object[checkbox_names[i]] = 1;
        } else {
          object[checkbox_names[i]] = 0;
        }
      }
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
          (data) => {
            displayMessageToUser(data);
          }
        );
      }
    });
  }
}

function populateTable(db_data) {
  var table = document.getElementById("data-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["id"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = dateConverter(db_data[i]["hunt_date"], true);

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
    tabCell.innerHTML = db_data[i]["hunt_close_time"];

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

function delMember(e) {
  const route = base_uri + "/" + subroute + "/" + e.currentTarget.my_id;

  if (
    window.confirm("You are about to delte a " + singular + ". Are you sure?")
  ) {
    callAPI(
      jwt_global,
      route,
      "DELETE",
      null,
      (data) => {
        localStorage.setItem("previous_action_message", data["message"]);
        window.scrollTo(0, 0);
        location.reload();
      },
      displayMessageToUser
    );
  }
}

function populateEdit(e) {
  const i = e.currentTarget.index;

  // disable the "Add" and enable the "Update"
  document.getElementById("btn-update").disabled = false;
  document.getElementById("btn-add").disabled = true;

  document.getElementById(singular + "-id").value = db_data[i]["id"];
  // lots more to add here
  document.getElementById("inp-hunt-date").value = dateConverter(
    db_data[i]["hunt_date"]
  );
  document.getElementById("select-status").value = db_data[i]["status"];

  document.getElementById("add-edit-form").scrollIntoView();
}
