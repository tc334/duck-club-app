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
var db_data_ponds;
const subroute = "scouts";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">add/edit scouting report</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
      
        <div class="form-row">
          <label for="report-id">Report ID</label>
          <input id="report-id" type="text" placeholder="n/a" name="id" disabled />
        </div>
    
        <div class="form-row">
          <label for="select-pond">Pond</label>
          <select id="select-pond" name="pond_id" required>
            <option value="">Select one</option>
          </select>
        </div>
    
        <div class="form-row">
          <label for="inp-count">count</label>
          <input
            id="inp-count"
            type="number"
            name="count"
          />
        </div>
    
        <div class="form-row">
          <label for="inp-notes">notes</label>
          <input
            id="inp-notes"
            type="text"
            name="notes"
          />
        </div>
    
        <span class="button-holder">
          <button class="btn--form" id="btn-add">Add</button>
          <button class="btn--form" id="btn-update" disabled>Update</button>
          <input class="btn--form" type="reset" />
        </span>
      </div>
    </form>
    </br>
    </br>
    </br>
    </br>
    
    <h1 class="heading-primary">scouting reports</h1>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <tr>
          <th>id</th>
          <th>property</th>
          <th>pond</th>
          <th>count</th>
          <th>notes</th>
          <th>scout</th>
          <th>actions</th>
        </tr>
      </table>
    </div>`;
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
    const route_1 = base_uri + "/ponds";
    callAPI(
      jwt,
      route_1,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["ponds"]) {
          db_data_ponds = response_full_json["ponds"];
          populatePondList_aux(db_data_ponds);
          const route = base_uri + "/" + subroute;
          callAPI(
            jwt,
            route,
            "GET",
            null,
            (response_full_json) => {
              if (response_full_json["data"]) {
                db_data = response_full_json["data"];
                populateTable(db_data);
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
          document.getElementById("report-id").value;

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
    tabCell.innerHTML = db_data[i]["id"].slice(0, 3);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["property"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["pond"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["count"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["notes"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["scout"];

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

  // need to convert pond name into id
  const pond_id = db_data_ponds.filter(function (pond) {
    return pond["name"] === db_data[i]["pond"];
  })[0]["id"];

  document.getElementById("report-id").value = db_data[i]["id"];
  document.getElementById("select-pond").value = pond_id;
  document.getElementById("inp-count").value = db_data[i]["count"];
  document.getElementById("inp-notes").value = db_data[i]["notes"];

  document.getElementById("add-edit-form").scrollIntoView();
}

function populatePondList_aux(db_data) {
  // sort ponds alphabetically
  db_data.sort(function (left, right) {
    return left["name"] > right["name"] ? 1 : -1;
  });
  const select_ponds = document.getElementById("select-pond");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = db_data[i]["name"];
    new_opt.value = db_data[i]["id"];
    select_ponds.appendChild(new_opt);
  }
}
