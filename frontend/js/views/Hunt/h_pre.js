import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  dateConverter_iso,
  decode_jwt,
  populate_aside_hunt,
} from "../../common_funcs.js";

var jwt_global;
var db_data_groupings;
var db_data_users;
var db_data_ponds;
var db_data_hunts;
var group_idx_to_id = [];
const subroute = "groupings";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">pre hunt</h1>
    <div id="status-table-container"></div>
    <div id="actions-button-holder" class="actions-button-holder"></div>
    <h1 class="heading-primary">groups</h1>
    <div id="tables-container"></div>
    
    <div id="join-modal" class="modal">
    <div class="modal-content">
      <span class="close">&times;</span>
      <h2 id="modal-group-heading"></h2>
      <form id="join-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <div class="form-row">
          <label for="inp-dog" class="chk-lbl">Dog</label>
          <input
            type="checkbox"
            id="inp-dog"
            name="b_dog"
          />
        </div>

        <div class="form-row">
          <label for="inp-atv-seats" class="chk-lbl"># ATV seats</label>
          <input
            type="number"
            id="inp-atv-seats"
            name="num_atv_seats"
            min="0"
            max="4"
            value="0"
          />
        </div>

        <div class="form-row">
          <label for="inp-pond-pref" class="chk-lbl">pond order</label>
          <textarea
            id="inp-pond-pref"
            name="pond_preference"
            placeholder="(optional) Wigeon, Forrest West, Remington, ..."
            rows="4"
            cols="40"></textarea>
        </div>

        <div class="form-row">
          <label for="inp-notes" class="chk-lbl">notes to draw manager</label>
          <textarea
            id="inp-notes"
            name="notes"
            placeholder="(optional)"
            rows="3"
            cols="40"></textarea>
        </div>
    
        <span class="button-holder">
          <button class="btn--form" id="btn-join">Join</button>
        </span>
      </div>
    </form>
    </div>
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

    // clear the aside
    var aside = document.getElementById("aside-content");
    //aside.innerHTML = "";

    // First step is to pull data from DB
    const route = base_uri + "/groupings/current";
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          db_data_groupings = response_full_json["data"]["groupings"];
          db_data_ponds = response_full_json["data"]["ponds"];
          db_data_hunts = response_full_json["data"]["hunt"];
          populateTables();
          const idxGroup_me = group_idx_to_id.indexOf(
            response_full_json["data"]["my_group_id"]
          );
          //console.log("Alpha");
          //console.log(db_data_hunts);
          populateStatusTable(
            db_data_hunts["hunt_date"],
            db_data_hunts["status"],
            response_full_json["data"]["my_group_id"],
            response_full_json["data"]["invite"]
          );
          selectCurrentPondAssignments();
          if (response_full_json["data"]["my_group_id"] > 0) {
            emphasizeUserGroupTable(idxGroup_me);
          }
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // What to do on a submit
    const myForm = document.getElementById("join-form");
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // find the user_id of the current user via public id
      const public_id = decode_jwt(jwt_global, "user");

      // Create a new group for this user
      var object = {
        public_id: public_id,
      };

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      formData.forEach((value, key) => (object[key] = value));

      var json = JSON.stringify(object);

      const route = base_uri + "/groupings";

      callAPI(
        jwt_global,
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

    // get the modal
    var modal = document.getElementById("join-modal");

    // get the span element that closes the modal
    var span = document.getElementsByClassName("close")[0];

    // When the user clicks on <span> (x), close the modal
    span.onclick = function () {
      modal.style.display = "none";
    };

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function (event) {
      if (event.target == modal) {
        modal.style.display = "none";
      }
    };
  }
}

function populateStatusTable(hunt_date, hunt_status, my_group_id, b_invite) {
  var container = document.getElementById("status-table-container");
  var table = document.createElement("table");
  table.classList.add("status-table");

  // hunt date
  var tr = table.insertRow(-1);
  var tabCell = tr.insertCell(-1);
  tabCell.classList.add("prehunt-summary-cell");
  tabCell.classList.add("prehunt-summary-cell-left");
  tabCell.innerHTML = "hunt date:";
  tabCell = tr.insertCell(-1);
  tabCell.classList.add("prehunt-summary-cell");
  tabCell.innerHTML = dateConverter_iso(hunt_date, true);

  // hunt status
  tr = table.insertRow(-1);
  tabCell = tr.insertCell(-1);
  tabCell.innerHTML = "hunt status:";
  tabCell.classList.add("prehunt-summary-cell");
  tabCell.classList.add("prehunt-summary-cell-left");
  tabCell = tr.insertCell(-1);
  tabCell.classList.add("prehunt-summary-cell");
  var postMessage;
  if (hunt_status == "signup_open") postMessage = "Signup is OPEN";
  else if (hunt_status == "signup_closed")
    postMessage = "Signup is CLOSED; draw in progress";
  else if (hunt_status == "draw_complete") postMessage = "Draw completed";
  tabCell.innerHTML = postMessage;

  // your status
  var tr = table.insertRow(-1);
  var tabCell = tr.insertCell(-1);
  tabCell.classList.add("prehunt-summary-cell");
  tabCell.classList.add("prehunt-summary-cell-left");
  tabCell.innerHTML = "your status:";
  tabCell = tr.insertCell(-1);
  tabCell.classList.add("prehunt-summary-cell");
  if (my_group_id > 0) {
    tabCell.innerHTML =
      "Signed up! (Group #" + (group_idx_to_id.indexOf(my_group_id) + 1) + ")";
  } else {
    tabCell.innerHTML = "Not hunting";
  }

  container.appendChild(table);

  if (hunt_status == "signup_open") {
    // action buttons
    var div = document.createElement("div");
    div.classList.add("div-actions-label");
    div.innerHTML = "Available actions:";
    container.appendChild(div);

    //div = document.createElement("div");
    //div.classList.add("actions-button-holder");
    div = document.getElementById("actions-button-holder");
    if (my_group_id > 0) {
      // withdraw button
      var btn_withdraw = document.createElement("button");
      btn_withdraw.group_id = my_group_id;
      btn_withdraw.innerHTML = "Withdraw From Hunt";
      btn_withdraw.classList.add("btn--form");
      btn_withdraw.addEventListener("click", withdraw);
      div.appendChild(btn_withdraw);
      // notification of invite
      if (b_invite) {
        var btn_invite = document.createElement("a");
        btn_invite.href = "#u_invitations";
        btn_invite.innerHTML = "You have an invitation!";
        btn_invite.classList.add("btn--form");
        div.appendChild(btn_invite);
      }
    } else {
      // join button
      var btn_join = document.createElement("button");
      btn_join.innerHTML = "Join";
      btn_join.className += "btn--form";
      btn_join.addEventListener("click", join);
      div.appendChild(btn_join);
    }
    container.appendChild(div);
  }
}

function populateTables() {
  var container = document.getElementById("tables-container");
  const column_headings = ["#", "hunters", "chip", "pond"];
  var select = document.getElementById("groupings-modal-select");

  for (var iGroup = 0; iGroup < db_data_groupings.length; iGroup++) {
    // this is a mapping of group index (1-N) to group id (from SQL)
    group_idx_to_id.push(db_data_groupings[iGroup]["id"]);

    // create a table for each grouping
    var table = document.createElement("table");
    table.id = "group-table-" + iGroup;

    // fill out header (same for each grouping)
    var tr = table.insertRow(-1);
    for (var iCol = 0; iCol < column_headings.length; iCol++) {
      var headerCell = document.createElement("TH");
      headerCell.innerHTML = column_headings[iCol];
      tr.appendChild(headerCell);
    }

    tr = table.insertRow(-1);

    var b_guests = false;
    if (db_data_groupings[iGroup]["guests"] != null) {
      b_guests = true;
    }

    // grouping label 1:N that makes sense to managers
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = iGroup + 1;

    // hunter
    var mem_str = "";
    for (
      var iMem = 0;
      iMem < db_data_groupings[iGroup]["members"].length;
      iMem++
    ) {
      mem_str += db_data_groupings[iGroup]["members"][iMem] + "<br>";
    }

    if (b_guests) {
      for (
        var iGst = 0;
        iGst < db_data_groupings[iGroup]["guests"].length;
        iGst++
      ) {
        mem_str += db_data_groupings[iGroup]["guests"][iGst] + "<br>";
      }
    }

    var tabCell = tr.insertCell(-1);
    tabCell.className += "hunters-column";
    tabCell.innerHTML = mem_str;

    // Chip
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data_groupings[iGroup]["chip"];
    container.appendChild(table);

    // Pond
    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("tr--pond-for-group");
    tabCell.id = "pond-for-group-" + iGroup;
    container.appendChild(table);
  }
}

function enableAllOptions() {
  var options = document.getElementsByClassName("opt-group-merge2");
  for (var i = 0; i < options.length; i++) {
    options[i].disabled = false;
  }
}

function selectCurrentPondAssignments() {
  for (var idxGroup = 0; idxGroup < db_data_groupings.length; idxGroup++) {
    if (db_data_groupings[idxGroup]["pond_id"] != null) {
      var elem = document.getElementById("pond-for-group-" + idxGroup);
      elem.innerHTML =
        db_data_ponds[
          findPondIndexFromID(db_data_groupings[idxGroup]["pond_id"])
        ]["name"];
    }
  }
}

function findPondIndexFromID(id) {
  for (var idxPond = 0; idxPond < db_data_ponds.length; idxPond++) {
    if (db_data_ponds[idxPond]["id"] == id) return idxPond;
  }
  // if you made it here, this was a fail
  return 0;
}

function emphasizeUserGroupTable(idxGroup) {
  var table = document.getElementById("group-table-" + idxGroup);
  table.classList.add("table-emphasize");
}

function withdraw(e) {
  const route = base_uri + "/groupings/withdraw";

  callAPI(
    jwt_global,
    route,
    "PUT",
    null,
    (data) => {
      localStorage.setItem("previous_action_message", data["message"]);
      window.scrollTo(0, 0);
      location.reload();
    },
    displayMessageToUser
  );
}

function join() {
  // turn the modal on
  document.getElementById("join-modal").style.display = "block";
}
