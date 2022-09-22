import AbstractView from "../../AbstractView.js";
import { base_uri } from "../../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside,
  decode_jwt,
  dateConverter_http,
} from "../../../common_funcs.js";

var jwt_global;
var db_data;
var db_data_ponds;
var db_data_users;
var db_data_dates;
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
      <h2 class="heading-secondary">Filters</h2>
      <form id="form-filter">
        <div class="filter-container">
          <section class="filter-date-exact">
            <select id="select-date" name="hunt_id" class="fixed-width-harvests">
              <option value=-1>--select hunt date--</option>
            </select>
          </section>
        </div>  
        <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
      </form>
    <h1 class="heading-primary">groups</h1>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <tr>
          <th>id</th>
          <th>pond</th>
          <th>slot 1</th>
          <th>slot 2</th>
          <th>slot 3</th>
          <th>slot 4</th>
          <th># hntrs</th>
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
        <div class="form-row">
          <label for="` +
      singular +
      `-id">Group ID</label>
          <input id="` +
      singular +
      `-id" type="text" placeholder="n/a" name="id" disabled />
        </div>
    
        <div class="form-row">
          <label for="select-pond">pond</label>
          <select id="select-pond" name="pond_id">
              <option value=-1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;--select pond--</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot1type">slot 1 type</label>
          <select id="select-slot1type" name="slot1_type" required>
            <option value="open">open</option>
            <option value="member">member</option>
            <option value="guest">guest</option>
            <option value="invitation">invitation</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot1-id">slot 1 hunter</label>
          <select id="select-slot1-id" name="slot1_id">
              <option value=-1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;--select member--</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot2type">slot 2 type</label>
          <select id="select-slot2type" name="slot2_type">
            <option value="open">open</option>
            <option value="member">member</option>
            <option value="guest">guest</option>
            <option value="invitation">invitation</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot2-id">slot 2 hunter</label>
          <select id="select-slot2-id" name="slot2_id">
              <option value=-1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;--select member--</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot3type">slot 3 type</label>
          <select id="select-slot3type" name="slot3_type">
            <option value="open">open</option>
            <option value="member">member</option>
            <option value="guest">guest</option>
            <option value="invitation">invitation</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot3-id">slot 3 hunter</label>
          <select id="select-slot3-id" name="slot3_id">
              <option value=-1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;--select member--</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot4type">slot 4 type</label>
          <select id="select-slot4type" name="slot4_type">
            <option value="open">open</option>
            <option value="member">member</option>
            <option value="guest">guest</option>
            <option value="invitation">invitation</option>
          </select>
        </div>

        <div class="form-row">
          <label for="select-slot4-id">slot 4 hunter</label>
          <select id="select-slot4-id" name="slot4_id">
              <option value=-1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;--select member--</option>
          </select>
        </div>

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

    // For this page, we also need to have the ponds db
    const route_2 = base_uri + "/" + "ponds";
    callAPI(
      jwt,
      route_2,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["ponds"]) {
          db_data_ponds = response_full_json["ponds"];
          const route_2_5 = base_uri + "/hunts/dates";
          callAPI(
            jwt,
            route_2_5,
            "GET",
            null,
            (response_full_json) => {
              if (response_full_json["dates"]) {
                db_data_dates = response_full_json["dates"];
                // For this page, we also need to have the birds db
                const route_3 = base_uri + "/" + "users";
                callAPI(
                  jwt,
                  route_3,
                  "GET",
                  null,
                  (response_full_json) => {
                    if (response_full_json["users"]) {
                      db_data_users = response_full_json["users"];
                      //console.log(db_data);
                      // now, only once harvests, ponds, & birds are successfully loaded, can we call the action
                      populatePondListBox();
                      populateUserListBox("select-slot1-id");
                      populateUserListBox("select-slot2-id");
                      populateUserListBox("select-slot3-id");
                      populateUserListBox("select-slot4-id");
                      populateDateList_aux(db_data_dates);
                    } else {
                      //console.log(data);
                    }
                  },
                  displayMessageToUser
                );
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

    // What do do on a filter apply
    const myFilterForm = document.getElementById("form-filter");
    myFilterForm.addEventListener("submit", function (e) {
      e.preventDefault();
      mySubmit(jwt, this);
    });

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

function lookUpPond(pond_id) {
  var i = 0;
  while (i < db_data_ponds.length) {
    if (db_data_ponds[i]["id"] == pond_id) {
      return db_data_ponds[i]["name"];
    }
    i = i + 1;
  }
  return "Unknown";
}

function lookUpMember(user_id) {
  var i = 0;
  while (i < db_data_users.length) {
    if (db_data_users[i]["id"] == user_id) {
      return (
        db_data_users[i]["first_name"] + " " + db_data_users[i]["last_name"]
      );
    }
    i = i + 1;
  }
  return "";
}

function populateTable(db_data) {
  console.log(db_data);
  var table = document.getElementById("data-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["group_id"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = lookUpPond(db_data[i]["pond_id"]);

    // slot 1
    var tabCell = tr.insertCell(-1);
    if (db_data[i]["slot1_type"] == "member") {
      tabCell.innerHTML = lookUpMember(db_data[i]["slot1_id"]);
    } else {
      tabCell.innerHTML = db_data[i]["slot1_type"];
    }

    // slot 2
    var tabCell = tr.insertCell(-1);
    if (db_data[i]["slot2_type"] == "member") {
      tabCell.innerHTML = lookUpMember(db_data[i]["slot2_id"]);
    } else {
      tabCell.innerHTML = db_data[i]["slot2_type"];
    }

    // slot 3
    var tabCell = tr.insertCell(-1);
    if (db_data[i]["slot3_type"] == "member") {
      tabCell.innerHTML = lookUpMember(db_data[i]["slot3_id"]);
    } else {
      tabCell.innerHTML = db_data[i]["slot3_type"];
    }

    // slot 4
    var tabCell = tr.insertCell(-1);
    if (db_data[i]["slot4_type"] == "member") {
      tabCell.innerHTML = lookUpMember(db_data[i]["slot4_id"]);
    } else {
      tabCell.innerHTML = db_data[i]["slot4_type"];
    }

    // # hunters
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["num_hunters"];

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
    btn_del.my_id = db_data[i]["group_id"];
    btn_del.innerHTML = "Del";
    btn_del.className += "btn--action";
    btn_del.addEventListener("click", delMember);
    tabCell.appendChild(btn_del);
  }
}

function delMember(e) {
  const route = base_uri + "/" + subroute + "/" + e.currentTarget.my_id;
  console.log("Alpha:" + route);
  console.log("Bravo" + e.currentTarget);

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

  document.getElementById(singular + "-id").value = db_data[i]["group_id"];
  //document.getElementById("inp-hunt-id").value = db_data[i]["hunt_id"];
  document.getElementById("select-pond").value = db_data[i]["pond_id"];

  document.getElementById("select-slot1type").value = db_data[i]["slot1_type"];
  document.getElementById("select-slot1-id").value = db_data[i]["slot1_id"];

  document.getElementById("select-slot2type").value = db_data[i]["slot2_type"];
  document.getElementById("select-slot2-id").value = db_data[i]["slot2_id"];

  document.getElementById("select-slot3type").value = db_data[i]["slot3_type"];
  document.getElementById("select-slot3-id").value = db_data[i]["slot3_id"];

  document.getElementById("select-slot4type").value = db_data[i]["slot4_type"];
  document.getElementById("select-slot4-id").value = db_data[i]["slot4_id"];

  document.getElementById("add-edit-form").scrollIntoView();
}

function populateDateList_aux(db_data) {
  const select_dates = document.getElementById("select-date");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = dateConverter_http(db_data[i]["hunt_date"]);
    new_opt.value = db_data[i]["id"];
    select_dates.appendChild(new_opt);
  }
}

function populatePondListBox() {
  var select_property = document.getElementById("select-pond");
  for (var i = 0; i < db_data_ponds.length; i++) {
    var option_new = document.createElement("option");
    option_new.value = db_data_ponds[i]["id"];
    option_new.innerHTML = db_data_ponds[i]["name"];
    select_property.appendChild(option_new);
  }
}

function populateUserListBox(select_id) {
  var select_property = document.getElementById(select_id);
  for (var i = 0; i < db_data_users.length; i++) {
    var option_new = document.createElement("option");
    option_new.value = db_data_users[i]["id"];
    option_new.innerHTML =
      db_data_users[i]["first_name"] + " " + db_data_users[i]["last_name"];
    select_property.appendChild(option_new);
  }
}

function mySubmit(jwt, myForm) {
  // Pull data from form and put it into the json format the DB wants
  const formData = new FormData(myForm);

  var object = {};
  formData.forEach((value, key) => (object[key] = value));

  // API route for this stats page
  const route =
    base_uri +
    "/" +
    subroute +
    "/filtered" +
    "?" +
    new URLSearchParams(object).toString();

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      db_data = data["groupings"];
      populateTable(db_data);
    },
    displayMessageToUser
  );
}
