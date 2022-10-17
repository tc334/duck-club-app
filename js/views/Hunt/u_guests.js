import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside,
  decode_jwt,
  populate_aside_hunt,
} from "../../common_funcs.js";

var jwt_global;
var db_data;
const subroute = "guests";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">Guests</h1>
    </br>
    <h3 class="heading-tertiary">your guests in the current hunt</h3>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <tr>
          <th>id</th>
          <th>name</th>
          <th>type</th>
          <th>actions</th>
        </tr>
      </table>
    </div>
    </br></br></br>
    
    
    <h3 class="heading-tertiary">add guest</h3>
    <form id="add-historical-form" name="edit-user" netlify>
    <div class="form-data-horizontal">
    
      <label for="select-guests">from your history</label>
      <select id="select-guests" name="guest_id" required>
        <option value="">Select one</option>
      </select>
      <button class="btn--form" id="btn-add-historical">Add</button>
  
    </div>
    </form>

    </br></br>

    <form id="add-new-form" name="edit-user" netlify>
    <div class="form-data-horizontal">
    
      <label for="inp-name">create new</label>
      <input
        id="inp-name"
        type="text"
        name="full_name"
        placeholder="Full Name"
      />

      <select id="select-type" name="type" required>
        <option value="">Select one</option>
        <option value="family">family</option>
        <option value="friend">friend</option>
      </select>
      <button class="btn--form" id="btn-add-new">Add</button>
  
    </div>
    </form>

    
    `;
  }

  js(jwt) {
    // this variable is copied into the higher namespace so I can get it
    // into the delete function
    jwt_global = jwt;

    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside_hunt(user_level);

    // First step is to pull data from DB
    const route_1 = base_uri + "/my_guests";
    callAPI(
      jwt,
      route_1,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          populateGuestList_aux(response_full_json["data"]["historical"]);
          populateTable(response_full_json["data"]["active"]);
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // CREATING NEW GUEST
    const myForm = document.getElementById("add-new-form");
    // What do do on a submit
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));
      var json = JSON.stringify(object);

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
    });

    // ADDING HISTORICAL GUEST
    const myForm_historical = document.getElementById("add-historical-form");
    // What do do on a submit
    myForm_historical.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));
      var json = JSON.stringify(object);

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
    });
  }
}

function populateTable(db_data) {
  var table = document.getElementById("data-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["id"].slice(0, 3);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["name"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["type"];

    var tabCell = tr.insertCell(-1);

    // Drop button
    var btn_del = document.createElement("button");
    btn_del.my_id = db_data[i]["id"];
    btn_del.innerHTML = "Drop";
    btn_del.className += "btn--action";
    btn_del.addEventListener("click", dropMember);
    tabCell.appendChild(btn_del);
  }
}

function dropMember(e) {
  const route = base_uri + "/" + "drop_guest" + "/" + e.currentTarget.my_id;
  const json = "{}";

  if (window.confirm("You are about to drop your guest. Are you sure?")) {
    callAPI(
      jwt_global,
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
}

function populateGuestList_aux(db_data) {
  // sort guests alphabetically
  db_data.sort(function (left, right) {
    return left["name"] > right["name"] ? 1 : -1;
  });
  const select_guests = document.getElementById("select-guests");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = db_data[i]["name"];
    new_opt.value = db_data[i]["id"];
    select_guests.appendChild(new_opt);
  }
}
