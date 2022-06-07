import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
} from "../common_funcs.js";

var jwt_global;
var db_data;
var db_data_ponds;
var db_data_birds;
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
    <div id="harvest-filter-container">
      <h1 class="heading-primary">filters</h1>
      <div class="harvest-filter">
        <div class="filter-date">
          <h2 class="heading-secondary">Date</h2>
          <div id="most-recent">
            <input type="checkbox" id="inp-mostrecent">
            <label for="inp-mostrecent">most recent hunt</label>
          </div>
          <div class="harvest-date">
            <input type="date" id="inp-date">
          </div>
        </div>
        <div class="filter-pond">
          <h2 class="heading-secondary">Pond</h2>
          <select id="select-pond">
            <option value="">All</option>
          </select>
        </div>
        <button class="btn--form" id="btn-filter">Apply</button>
      </div>
    </div>
    <h1 class="heading-primary">harvests</h1>
    <table id="` +
      singular +
      `-table">
      <tr>
        <th>id</th>
        <th>date</th>
        <th>pond</th>
        <th>hunters</th>
        <th>bird</th>
        <th>count</th>
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
      `-id">Harvest ID</label>
        <input id="` +
      singular +
      `-id" type="text" placeholder="n/a" name="id" disabled />
    
        <label for="inp-groupid">Group ID</label>
        <input
          id="inp-groupid"
          type="number"
          name="group_id"
          disabled
        />
    
        <label for="select-bird">Bird</label>
        <select id="select-bird" name="bird_id" required>
          <option value="">Select one</option>
        </select>
    
        <label for="inp-count">Count</label>
        <input
          id="inp-count"
          type="number"
          name="count"
          required
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
                      console.log("Alpha");
                      console.log(db_data);
                      // now, only once harvests, ponds, & birds are successfully loaded, can we call the action
                      populateTable(db_data);
                      populatePondListBox();
                      populateBirdListBox();
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
  var table = document.getElementById(singular + "-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["id"];

    // date
    var tabCell = tr.insertCell(-1);
    const thisDate = new Date(db_data[i]["hunt_date"]);
    tabCell.innerHTML =
      thisDate.getFullYear() +
      "-" +
      thisDate.getMonth() +
      "-" +
      thisDate.getDay();

    // pond
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = "TBD";

    // hunters
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = "TBD";

    // bird
    var tabCell = tr.insertCell(-1);
    tabCell.className += "tr--bird-name";
    tabCell.innerHTML = db_data[i]["bird"];

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
    option_new.value = db_data_ponds[i]["name"];
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

  document.getElementById(singular + "-id").value = db_data[i]["id"];
  document.getElementById("inp-groupid").value = db_data[i]["group_id"];
  document.getElementById("inp-count").value = db_data[i]["count"];
  document.getElementById("select-bird").value = db_data[i]["bird"];

  document.getElementById("add-edit-form").scrollIntoView();
}
