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
const subroute = "groupings";
const singular = "grouping";
const plural = "groupings";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return (
      `<div class="reload-message"></div>
    <h1 class="heading-primary">groups</h1>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <tr>
          <th>id</th>
          <th>hunt</th>
          <th>pond</th>
          <th>slot 1</th>
          <th>slot 2</th>
          <th>slot 3</th>
          <th>slot 4</th>
          <th>#</th>
          <th>duck</th>
          <th>non</th>
          <th>actions</th>
        </tr>
      </table>
    </div>

    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">add/edit ` +
      singular +
      `</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <label for="` +
      singular +
      `-id">Group ID</label>
        <input id="` +
      singular +
      `-id" type="text" placeholder="n/a" name="id" disabled />
    
        <label for="inp-hunt-id">hunt ID</label>
        <input
          id="inp-hunt-id"
          type="number"
          name="hunt_id"
          required
        />

        <label for="inp-pon-id">pond ID</label>
        <input
          id="inp-pond-id"
          type="number"
          name="pond_id"
        />

        <label for="select-slot1type">slot 1 type</label>
        <select id="select-slot1type" name="slot1_type" required>
          <option value="open">open</option>
          <option value="member">member</option>
          <option value="guest">guest</option>
          <option value="invitation">invitation</option>
        </select>

        <label for="inp-slot1-id">slot 1 ID</label>
        <input
          id="inp-slot1-id"
          type="number"
          name="slot1_id"
          required
        />

        <label for="select-slot2type">slot 2 type</label>
        <select id="select-slot2type" name="slot2_type">
          <option value="open">open</option>
          <option value="member">member</option>
          <option value="guest">guest</option>
          <option value="invitation">invitation</option>
        </select>

        <label for="inp-slot2-id">slot 2 ID</label>
        <input
          id="inp-slot2-id"
          type="number"
          name="slot2_id"
        />

        <label for="select-slot3type">slot 3 type</label>
        <select id="select-slot3type" name="slot3_type">
          <option value="open">open</option>
          <option value="member">member</option>
          <option value="guest">guest</option>
          <option value="invitation">invitation</option>
        </select>

        <label for="inp-slot3-id">slot 3 ID</label>
        <input
          id="inp-slot3-id"
          type="number"
          name="slot3_id"
        />

        <label for="select-slot4type">slot 4 type</label>
        <select id="select-slot4type" name="slot4_type">
          <option value="open">open</option>
          <option value="member">member</option>
          <option value="guest">guest</option>
          <option value="invitation">invitation</option>
        </select>

        <label for="inp-slot4-id">slot 4 ID</label>
        <input
          id="inp-slot4-id"
          type="number"
          name="slot4_id"
        />

        <span class="button-holder">
          <button class="btn--form" id="btn-add">Add</button>
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
        if (response_full_json[plural]) {
          db_data = response_full_json[plural];
          populateTable(db_data);
        } else {
          // ?
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
      formData.forEach((value, key) => {
        if (value != null && value.length > 0) object[key] = value;
      });

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
    tabCell.innerHTML = db_data[i]["hunt_id"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["pond_id"];

    // slot 1
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML =
      db_data[i]["slot1_type"] + " - " + db_data[i]["slot1_id"];

    // slot 2
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML =
      db_data[i]["slot2_type"] + " - " + db_data[i]["slot2_id"];

    // slot 3
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML =
      db_data[i]["slot3_type"] + " - " + db_data[i]["slot3_id"];

    // slot 4
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML =
      db_data[i]["slot4_type"] + " - " + db_data[i]["slot4_id"];

    // # hunters
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["num_hunters"];

    // duck average
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["harvest_ave_ducks"];

    // duck average
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["harvest_ave_non"];

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
  document.getElementById("inp-hunt-id").value = db_data[i]["hunt_id"];
  document.getElementById("inp-pond-id").value = db_data[i]["pond_id"];
  document.getElementById("select-slot1type").value = db_data[i]["slot1_type"];
  document.getElementById("inp-slot1-id").value = db_data[i]["slot1_id"];

  document.getElementById("select-slot2type").value = db_data[i]["slot2_type"];
  document.getElementById("inp-slot2-id").value = db_data[i]["slot2_id"];

  document.getElementById("select-slot3type").value = db_data[i]["slot3_type"];
  document.getElementById("inp-slot3-id").value = db_data[i]["slot3_id"];

  document.getElementById("select-slot4type").value = db_data[i]["slot4_type"];
  document.getElementById("inp-slot4-id").value = db_data[i]["slot4_id"];

  document.getElementById("add-edit-form").scrollIntoView();
}
