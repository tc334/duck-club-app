import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
} from "../common_funcs.js";

var jwt_global;
var db_data;
var db_data_properties;
const subroute = "ponds";
const singular = "pond";
const plural = "ponds";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return (
      `<div class="reload-message"></div>
    <h1 class="heading-primary">ponds</h1>
    <table id="` +
      singular +
      `-table">
      <tr>
        <th>id</th>
        <th>name</th>
        <th>property</th>
        <th>status</th>
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
      `-id">Pond ID</label>
        <input id="` +
      singular +
      `-id" type="text" placeholder="n/a" name="id" disabled />
    
        <label for="` +
      singular +
      `-name">` +
      singular +
      ` Name</label>
        <input
          id="` +
      singular +
      `-name"
          type="text"
          name="name"
          required
        />
    
        <label for="select-property">Property</label>
        <select id="select-property" name="property_id" required>
          <option value="">Select one</option>
        </select>
    
        <label for="select-status">Status</label>
        <select id="select-status" name="status" required>
          <option value="">Select one</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </select>
    
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
          // For the ponds page, we also need to have the properties db
          const route_2 = base_uri + "/" + "properties";
          callAPI(
            jwt,
            route_2,
            "GET",
            null,
            (response_full_json) => {
              if (response_full_json["properties"]) {
                db_data_properties = response_full_json["properties"];
                // now, only once both ponds & properties are successfully loaded, can we call the action
                populateTable(db_data);
                populatePropertyListBox();
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

      // for ponds, we need to extract the property["id"] from what we currently have, which is the property["name"]
      const searchResult = db_data_properties.filter(function (property) {
        return property["name"] === object["property_id"];
      })[0]["id"];
      object["property_id"] = searchResult;

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

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["name"];

    var tabCell = tr.insertCell(-1);
    // match up the corresponding property name
    const searchResult = db_data_properties.filter(function (property) {
      return property["id"] === db_data[i]["property_id"];
    });
    var propertyName = "undefined";
    if (searchResult.length == 1) {
      propertyName = searchResult[0]["name"];
    }
    tabCell.innerHTML = propertyName;

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["status"];

    var tabCell = tr.insertCell(-1);

    // Edit button
    var btn_edt = document.createElement("button");
    btn_edt.index = i;
    btn_edt.property_name = propertyName;
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

function populatePropertyListBox() {
  var select_property = document.getElementById("select-property");
  for (var i = 0; i < db_data_properties.length; i++) {
    var option_new = document.createElement("option");
    option_new.value = db_data_properties[i]["name"];
    option_new.innerHTML = db_data_properties[i]["name"];
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
  document.getElementById(singular + "-name").value = db_data[i]["name"];
  document.getElementById("select-property").value =
    e.currentTarget.property_name;
  document.getElementById("select-status").value = db_data[i]["status"];

  document.getElementById("add-edit-form").scrollIntoView();
}
