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
var db_data_users;
const subroute = "guests";
const singular = "guest";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
      <h2 class="heading-secondary">Filters</h2>
      <form id="form-filter">
        <div class="filter-container">
          <section class="filter-date-exact">
            <select id="select-user" name="user_id" class="fixed-width-harvests">
              <option value=-1>--select member--</option>
            </select>
          </section>
        </div>  
        <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
      </form>
    <h1 class="heading-primary">guests</h1>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <tr>
          <th>id</th>
          <th>guest</th>
          <th>member</th>
          <th>date</th>
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
    populate_aside(user_level);

    // For this page, we also need to have the ponds db
    const route_2 = base_uri + "/" + "users";
    callAPI(
      jwt,
      route_2,
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

    // What do do on a filter apply
    const myFilterForm = document.getElementById("form-filter");
    myFilterForm.addEventListener("submit", function (e) {
      e.preventDefault();
      mySubmit(jwt, this);
    });
  }
}

function populateTable(db_data) {
  console.log(db_data);
  var table = document.getElementById("data-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["participant_id"].slice(0, 3);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["guest"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["member"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = dateConverter_http(db_data[i]["date"], false);

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
  const hunt_id = db_data[i]["hunt_id"];
  const guest_id = db_data[i]["guest_id"];

  const route = base_uri + "/drop_guest/" + guest_id;
  console.log("Alpha:" + route);

  const object = {
    hunt_id: hunt_id,
  };
  var json = JSON.stringify(object);

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

function mySubmit(jwt, myForm) {
  const public_id = document.getElementById("select-user").value;

  // API route for this stats page
  const route = base_uri + "/" + subroute + "/" + public_id;

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      db_data = data["data"];
      populateTable(db_data);
    },
    displayMessageToUser
  );
}
