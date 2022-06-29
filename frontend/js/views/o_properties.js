import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside,
  decode_jwt,
} from "../common_funcs.js";

var jwt_global;
var db_data;
const subroute = "properties";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">properties</h1>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <tr>
          <th>id</th>
          <th>name</th>
          <th>region</th>
          <th>actions</th>
        </tr>
      </table>
    </div>
    
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">add/edit property</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <label for="property-id">Property ID</label>
        <input id="property-id" type="text" placeholder="n/a" name="id" disabled />
    
        <label for="property-name">Property Name</label>
        <input
          id="property-name"
          type="text"
          name="name"
          required
        />
    
        <label for="select-region">Region</label>
        <select id="select-region" name="region" required>
          <option value="">Select one</option>
          <option value="Northern">Northern</option>
          <option value="Southern">Southern</option>
        </select>
    
        <span class="button-holder">
          <button class="btn--form" id="btn-add">Add</button>
          <button class="btn--form" id="btn-update" disabled>Update</button>
          <input class="btn--form" type="reset" />
        </span>
      </div>
    </form>`;
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
    });

    // What do do on a submit
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));
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
          document.getElementById("property-id").value;

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
    tabCell.innerHTML = db_data[i]["name"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["region"];

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

  if (window.confirm("You are about to delte a property. Are you sure?")) {
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

  document.getElementById("property-id").value = db_data[i]["id"];
  document.getElementById("property-name").value = db_data[i]["name"];
  document.getElementById("select-region").value = db_data[i]["region"];

  document.getElementById("add-edit-form").scrollIntoView();
}
