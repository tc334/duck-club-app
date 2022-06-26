import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  formatDate,
  dateConverter,
  populate_aside,
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
    <div class="hunt-list" id="foo300">
      <span>active hunts:</span>
      <select id="select-hunt"></select>
    </div>
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

        <label for="inp-signup-close-auto" class="chk-lbl">automatically close signup</label>
        <input
          type="checkbox"
          id="inp-signup-close-auto"
          name="signup_closed_auto"
          checked="true"
        />

        <label for="inp-signup-close-time" class="chk-lbl">signup close time</label>
        <input
          id="inp-signup-close-time"
          type="time"
          value="18:00"
          name="signup_closed_time"
        />
    
        <label for="inp-draw-auto" class="chk-lbl">auto draw</label>
        <input type="checkbox" id="inp-draw-auto" disabled/>

        <label for="inp-hunt-open-auto" class="chk-lbl">automatically open hunt</label>
        <input
          type="checkbox"
          id="inp-hunt-open-auto"
          name="hunt_open_auto"
          checked
        />

        <label for="inp-hunt-open-time">hunt open time</label>
        <input
          id="inp-hunt-open-time"
          type="time"
          value="06:00"
          name="hunt_open_time"
        />
    
        <label for="inp-hunt-close-auto" class="chk-lbl">automatically close hunt</label>
        <input
          type="checkbox"
          id="inp-hunt-close-auto"
          name="hunt_close_auto"
          checked
        />

        <label for="inp-hunt-close-time">hunt close time</label>
        <input
          id="inp-hunt-close-time"
          type="time"
          value="19:00"
          name="hunt_close_time"
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

    // set the date in the add/edit form to today
    setDefaultDate();

    // First step is to pull data from DB
    const route = base_uri + "/" + subroute + "/active";
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json[subroute]) {
          db_data = response_full_json[subroute];
          const idxMostRecent = db_data.length - 1;
          populateEdit(idxMostRecent); // populate with the last entry in the db, which is the most recently started hunt
          populateHuntListBox(idxMostRecent);
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

    document.getElementById("select-hunt").addEventListener("change", () => {
      populateEdit(document.getElementById("select-hunt").value);
    });
  }
}

function populateHuntListBox(idxSelected) {
  var select = document.getElementById("select-hunt");
  for (var i = db_data.length - 1; i >= 0; i--) {
    var option_new = document.createElement("option");
    option_new.value = i;
    option_new.innerHTML = dateConverter(db_data[i]["hunt_date"], true);
    select.appendChild(option_new);
  }
  if (idxSelected >= 0) {
    select.value = idxSelected;
  }
}

function populateEdit(i) {
  // if there are hunts open, we will initially populate with the most recent
  if (i >= 0) {
    // disable the "Add" and enable the "Update"
    document.getElementById("btn-update").disabled = false;
    document.getElementById("btn-add").disabled = true;

    document.getElementById(singular + "-id").value = db_data[i]["id"];
    // lots more to add here
    document.getElementById("inp-hunt-date").value = dateConverter(
      db_data[i]["hunt_date"]
    );
    document.getElementById("select-status").value = db_data[i]["status"];
    document.getElementById("inp-signup-close-auto").checked =
      db_data[i]["signup_closed_auto"] == 1 ? true : false;
    document.getElementById("inp-draw-auto").checked =
      db_data[i]["draw_mehtod_auto"] == 1 ? true : false;
    document.getElementById("inp-hunt-open-auto").checked =
      db_data[i]["hunt_open_auto"] == 1 ? true : false;
    document.getElementById("inp-hunt-open-auto").checked =
      db_data[i]["hunt_close_auto"] == 1 ? true : false;
    document.getElementById("inp-signup-close-time").value =
      db_data[i]["signup_closed_time"];
    document.getElementById("inp-hunt-open-time").value =
      db_data[i]["hunt_open_time"];
    document.getElementById("inp-hunt-close-time").value =
      db_data[i]["hunt_close_time"];

    document.getElementById("add-edit-form").scrollIntoView();
  } else {
    // There aren't any hunts open, so the form will remain in the "add" state
  }
}

function setDefaultDate() {
  const dateTime = new Date();
  const dateTime_central = dateTime.toLocaleString("en-US", {
    timeZone: "America/Chicago",
  });
  const date_formatted = formatDate(dateTime_central);

  document.getElementById("inp-hunt-date").value = date_formatted;
}
