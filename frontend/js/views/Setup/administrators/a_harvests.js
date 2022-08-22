import AbstractView from "../../AbstractView.js";
import { base_uri } from "../../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  decode_jwt,
  populate_aside,
  dateConverter_http,
  removeAllChildNodes,
} from "../../../common_funcs.js";

var jwt_global;
var db_data;
var db_data_ponds;
var db_data_birds;
var db_data_dates;
const subroute = "harvests";
const singular = "harvest";
const plural = "harvests";

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
          <section class="filter-pond">
            <select id="select-pond" name="pond_id" class="fixed-width-harvests">
              <option value=-1>&nbsp;&nbsp;&nbsp;--select pond--</option>
            </select>
          </section>
        </div>  
        <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
      </form>
    <h1 class="heading-primary">harvests</h1>
    <div class="table-overflow-wrapper">
      <table>
        <thead>
          <tr>
            <th>id</th>
            <th>date</th>
            <th>pond</th>
            <th>group id</th>
            <th>bird</th>
            <th>count</th>
            <th>actions</th>
          </tr>
        </thead>
        <tbody id="` +
      singular +
      `-table">
        </tbody>
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
      `-id">Harvest ID</label>
          <input id="` +
      singular +
      `-id" type="text" placeholder="n/a" name="id" disabled />
        </div>
    
        <div class="form-row">
          <label for="inp-groupid">Group ID</label>
          <input
            id="inp-groupid"
            type="number"
            name="group_id"
          />
        </div>
    
        <div class="form-row">
          <label for="select-bird">Bird</label>
          <select id="select-bird" name="bird_id" required>
            <option value="">Select one</option>
          </select>
        </div>
    
        <div class="form-row">
          <label for="inp-count">Count</label>
          <input
            id="inp-count"
            type="number"
            name="count"
            required
          />
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
                const route_3 = base_uri + "/" + "birds";
                callAPI(
                  jwt,
                  route_3,
                  "GET",
                  null,
                  (response_full_json) => {
                    if (response_full_json["birds"]) {
                      db_data_birds = response_full_json["birds"];
                      //console.log(db_data);
                      // now, only once harvests, ponds, & birds are successfully loaded, can we call the action
                      populatePondListBox();
                      populateBirdListBox();
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

      // for birds, we need to extract the bird["id"] from what we currently have, which is the bird["name"]
      const searchResult = db_data_birds.filter(function (bird) {
        return bird["name"] === object["bird_id"];
      })[0]["id"];
      object["bird_id"] = searchResult;

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
        const route = base_uri + "/" + subroute;

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

    // What do do on a submit
    const myForm2 = document.getElementById("form-filter");
    myForm2.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

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
          db_data = data["harvests"];
          populateTable(data["harvests"]);
        },
        displayMessageToUser
      );
    });
  }
}

function populateTable(db_data) {
  var table = document.getElementById(singular + "-table");
  removeAllChildNodes(table);

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["harvest_id"].slice(0, 3);

    // date
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = dateConverter_http(db_data[i]["hunt_date"]);

    // pond
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["pond_name"];

    // group id
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["group_id"];

    // bird
    var tabCell = tr.insertCell(-1);
    tabCell.className += "tr--bird-name";
    tabCell.innerHTML = db_data[i]["bird_name"];

    // count
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["count"];

    // action
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

function populateBirdListBox() {
  var select_property = document.getElementById("select-bird");
  for (var i = 0; i < db_data_birds.length; i++) {
    var option_new = document.createElement("option");
    option_new.value = db_data_birds[i]["name"];
    option_new.innerHTML = db_data_birds[i]["name"];
    option_new.className += "tr--bird-name";
    select_property.appendChild(option_new);
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

  document.getElementById(singular + "-id").value = db_data[i]["harvest_id"];
  document.getElementById("inp-groupid").value = db_data[i]["group_id"];
  document.getElementById("inp-count").value = db_data[i]["count"];
  document.getElementById("select-bird").value = db_data[i]["bird_name"];

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
