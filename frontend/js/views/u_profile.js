import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  decode_jwt,
  populate_aside,
} from "../common_funcs.js";

var jwt_global;
var db_data;
const subroute = "users";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">your profile</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <div class="form-row">
          <label for="user-id">User ID</label>
          <input id="user-id" type="text" placeholder="n/a" name="id" disabled />
        </div>
    
        <div class="form-row">
          <label for="first-name">First Name</label>
          <input
            id="first-name"
            type="text"
            name="first_name"
            required
          />
        </div>
    
        <div class="form-row">
          <label for="last-name">Last Name</label>
          <input
            id="last-name"
            type="text"
            name="last_name"
            required
          />
        </div>
    
        <div class="form-row">
          <label for="email">Email address</label>
          <input
            id="email"
            type="email"
            name="email"
            required
          />
        </div>
    
        <div class="form-row">
          <label for="inp-level">Membership Level</label>
          <input id="inp-level" type="text" name="inp-level" disabled />
        </div>
    
        <div class="form-row">
          <label for="inp-status">Membership Status</label>
          <input id="inp-status" type="text" name="inp-status" disabled />
        </div>
    
        <div class="form-row">
          <label for="inp-balance">Balance</label>
          <input id="inp-balance" type="text" name="inp-balance" disabled />
        </div>
    
        <span class="button-holder">
          <button class="btn--form" id="btn-update">Update</button>
        </span>
      </div>
    </form>`;
  }

  js(jwt) {
    // this variable is copied into the higher namespace so I can get it
    // into the delete function
    jwt_global = jwt;
    const public_id = decode_jwt(jwt, "user");

    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside(user_level);

    // First step is to pull data from DB
    const route = base_uri + "/" + subroute + "/" + public_id;

    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["user"]) {
          db_data = response_full_json["user"];
          populateEdit(db_data);
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // What do do on a submit
    const myForm = document.getElementById("add-edit-form");
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));
      var json = JSON.stringify(object);

      // attach the users public-id to the json & send at PUT instead of POST
      const route = base_uri + "/" + subroute + "/" + public_id;

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
    });
  }
}

function populateEdit(db_data) {
  document.getElementById("user-id").value = db_data["id"];
  document.getElementById("first-name").value = db_data["first_name"];
  document.getElementById("last-name").value = db_data["last_name"];
  document.getElementById("email").value = db_data["email"];
  document.getElementById("inp-level").value = db_data["level"];
  document.getElementById("inp-status").value = db_data["status"];
  document.getElementById("inp-balance").value =
    "$" + db_data["outstanding_balance"];

  document.getElementById("add-edit-form").scrollIntoView();
}
