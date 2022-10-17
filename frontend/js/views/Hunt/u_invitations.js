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
const subroute = "invitations";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">Invitations</h1>
    </br>
    <h3 class="heading-tertiary">from you</h3>
    <div class="table-overflow-wrapper">
      <table id="data-table-from">
        <tr>
          <th>id</th>
          <th>invitee</th>
          <th>status</th>
          <th>actions</th>
          <th>notes</th>
        </tr>
      </table>
    </div>
    </br>
    </br>
    <h3 class="heading-tertiary">to you</h3>
    <div class="table-overflow-wrapper">
      <table id="data-table-to">
        <tr>
          <th>id</th>
          <th>inviter</th>
          <th>actions</th>
        </tr>
      </table>
    </div>
    </br></br></br>
    
    
    <h3 class="heading-tertiary">send invite</h3>
    <form id="add-invite-form" name="edit-user" netlify>
      <div class="form-data-horizontal">
    
        <label for="select-invitee">hunters signed up for current hunt</label>
        <select id="select-invitee" name="public_id" required>
          <option value="">Select one</option>
        </select>
        <button class="btn--form" id="btn-add-invitee">Add</button>

      </div>
    </form>

    `;
  }

  js(jwt) {
    jwt_global = jwt;

    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside_hunt(user_level);

    // First step is to pull data from DB
    const route_1 = base_uri + "/" + subroute;

    callAPI(
      jwt,
      route_1,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          //console.log(response_full_json["data"]);
          populateJoinedList_aux(response_full_json["data"]["users"]);
          populateTable_from(response_full_json["data"]["invitations_from"]);
          populateTable_to(response_full_json["data"]["invitations_to"]);
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // CREATING NEW INVITE
    const myForm = document.getElementById("add-invite-form");
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
  }
}

function populateTable_from(db_data) {
  var table = document.getElementById("data-table-from");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["id"].slice(0, 3);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["name"];

    var tabCell = tr.insertCell(-1);
    if (db_data[i]["active"]) {
      tabCell.innerHTML = "active";
    } else {
      tabCell.innerHTML = "closed";
    }

    var tabCell = tr.insertCell(-1);
    if (db_data[i]["active"]) {
      // Drop button
      var btn_del = document.createElement("button");
      btn_del.my_id = db_data[i]["id"];
      btn_del.innerHTML = "Rescind";
      btn_del.className += "btn--action";
      btn_del.addEventListener("click", rescindInvite);
      tabCell.appendChild(btn_del);
    }

    var tabCell = tr.insertCell(-1);
    tabCell.className += "invitation-notes";
    if (db_data[i]["notes"] != null) {
      tabCell.innerHTML = db_data[i]["notes"];
    }
  }
}

function rescindInvite(e) {
  const route =
    base_uri + "/" + subroute + "/rescind" + "/" + e.currentTarget.my_id;
  const json = "{}";

  if (
    window.confirm("You are about to rescind your invitation. Are you sure?")
  ) {
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

function rejectInvite(e) {
  const route =
    base_uri + "/" + subroute + "/reject" + "/" + e.currentTarget.my_id;
  const json = "{}";

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

function acceptInvite(e) {
  const route =
    base_uri + "/" + subroute + "/accept" + "/" + e.currentTarget.my_id;
  const json = "{}";

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

function populateJoinedList_aux(db_data) {
  // sort alphabetically
  db_data.sort(function (left, right) {
    return left["name"] > right["name"] ? 1 : -1;
  });
  const select = document.getElementById("select-invitee");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = db_data[i]["name"];
    new_opt.value = db_data[i]["id"];
    select.appendChild(new_opt);
  }
}

function populateTable_to(db_data) {
  var table = document.getElementById("data-table-to");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["id"].slice(0, 3);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["name"];

    var tabCell = tr.insertCell(-1);

    // Accept button
    var btn_accept = document.createElement("button");
    btn_accept.my_id = db_data[i]["id"];
    btn_accept.innerHTML = "Accept";
    btn_accept.className += "btn--action";
    btn_accept.addEventListener("click", acceptInvite);
    tabCell.appendChild(btn_accept);

    // Slash
    tabCell.insertAdjacentText("beforeend", "\x2F");

    // Reject button
    var btn_reject = document.createElement("button");
    btn_reject.my_id = db_data[i]["id"];
    btn_reject.innerHTML = "Reject";
    btn_reject.className += "btn--action";
    btn_reject.addEventListener("click", rejectInvite);
    tabCell.appendChild(btn_reject);
  }
}
