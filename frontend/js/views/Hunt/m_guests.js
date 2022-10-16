import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  decode_jwt,
  dateConverter_http,
  populate_aside_hunt,
} from "../../common_funcs.js";

var jwt_global;
var db_data_users;
var db_data_guests;
const subroute = "guests";
const singular = "guest";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return (
      `<div class="reload-message"></div>
    <h1 class="heading-primary">current guests</h1>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <tr>
          <th>id</th>
          <th>guest</th>
          <th>type</th>
          <th>member</th>
          <th>actions</th>
        </tr>
      </table>
    </div>
    
    <!-- ADD GUEST FORM -->
    <h1 class="heading-primary">add ` +
      singular +
      `</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">

        <div class="form-row">
          <label for="inp-name">full name</label>
          <input id="inp-name" type="text" placeholder="John Doe" name="full_name" required />
        </div>
          
        <div class="form-row">
          <label for="select-type">Type</label>
          <select id="select-type" name="type" required>
            <option value="">Select one</option>
            <option value="family">Family</option>
            <option value="friend">Friend</option>
          </select>
        </div>
    
        <div class="form-row">
          <label for="select-user">Host</label>
          <select id="select-user" name="public_id" required>
            <option value="">Select one</option>
          </select>
        </div>
    
        <span class="button-holder">
          <button class="btn--form" id="btn-add">Add</button>
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
    populate_aside_hunt(user_level);

    // For this page, we also need to have the ponds db
    const route_2 = base_uri + "/" + "guests";
    callAPI(
      jwt,
      route_2,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          db_data_guests = response_full_json["data"];
          populateTable(db_data_guests);

          const route_1 = base_uri + "/users/active";
          callAPI(
            jwt,
            route_1,
            "GET",
            null,
            (response_full_json) => {
              if (response_full_json["users"]) {
                db_data_users = response_full_json["users"];
                populateUserList_aux(db_data_users);
              } else {
                //console.log(data);
              }
            },
            displayMessageToUser
          );
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // What do do on a "add"
    const myForm = document.getElementById("add-edit-form");
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));

      // now we can stringify the json just like we do on the other views
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
    tabCell.innerHTML = db_data[i]["host"];

    var tabCell = tr.insertCell(-1);

    // Delete button
    var btn_del = document.createElement("button");
    btn_del.my_idx = i;
    btn_del.innerHTML = "Del";
    btn_del.className += "btn--action";
    btn_del.addEventListener("click", delMember);
    tabCell.appendChild(btn_del);
  }
}

function delMember(e) {
  const i = e.currentTarget.my_idx;
  const guest_id = db_data[i]["guest_id"];

  const route = base_uri + "/drop_guest/" + guest_id;

  var json = "{}";

  if (window.confirm("You are about to delte a guest hunt. Are you sure?")) {
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

function populateUserList_aux(db_data) {
  const select_users = document.getElementById("select-user");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML =
      db_data[i]["first_name"] + " " + db_data[i]["last_name"];
    new_opt.value = db_data[i]["public_id"];
    select_users.appendChild(new_opt);
  }
}
