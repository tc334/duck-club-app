import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  dateConverter_iso,
  decode_jwt,
  populate_aside,
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
    <div id="tables-container"></div>`;
  }

  js(jwt) {
    // this variable is copied into the higher namespace so I can get it
    // into the delete function
    jwt_global = jwt;

    // check for reload message; if exists, display
    reloadMessage();

    // clear the aside
    var aside = document.getElementById("aside-content");
    aside.innerHTML = "";

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
          db_data_users = response_full_json["data"]["users"];
          db_data_ponds = response_full_json["data"]["ponds"];
          db_data_hunts = response_full_json["data"]["hunts"];
          populateTables();
          const idxGroup_me = group_idx_to_id.indexOf(
            response_full_json["data"]["my_group_id"]
          );
          populateStatusTable(
            db_data_hunts["hunt_date"],
            db_data_hunts["status"],
            response_full_json["data"]["my_group_id"]
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
  }
}

function populateStatusTable(hunt_date, hunt_status, my_group_id) {
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
      btn_withdraw.className += "btn--form";
      btn_withdraw.addEventListener("click", withdraw);
      div.appendChild(btn_withdraw);
      // add guest button
      var btn_addGuest = document.createElement("button");
      btn_addGuest.innerHTML = "Add Guest(s)";
      btn_addGuest.className += "btn--form";
      btn_addGuest.disabled = true;
      //btn_addGuest.addEventListener("click", withdraw);
      div.appendChild(btn_addGuest);
      // add guest button
      var btn_invite = document.createElement("button");
      btn_invite.innerHTML = "Invite Member to Join Your Group";
      btn_invite.className += "btn--form";
      btn_invite.disabled = true;
      //btn_invite.addEventListener("click", withdraw);
      div.appendChild(btn_invite);
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
  const column_headings = ["#", "hunters", "pond"];
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

    // grouping label 1:N that makes sense to managers
    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = iGroup + 1;

    // Hunters
    var tabCell = tr.insertCell(-1);
    var hunter_names = "";
    for (var iHunter = 0; iHunter < 4; iHunter++) {
      if (
        db_data_groupings[iGroup]["slot" + (iHunter + 1) + "_type"] == "member"
      ) {
        const user_id =
          db_data_groupings[iGroup]["slot" + (iHunter + 1) + "_id"];
        const user_full_name = getUserFullName(user_id);
        if (hunter_names.length > 0) {
          hunter_names = hunter_names.concat("\n" + user_full_name);
        } else {
          hunter_names = hunter_names.concat(user_full_name);
        }
      }
    }
    tabCell.className += "hunters-column";
    tabCell.innerHTML = hunter_names;

    // Pond
    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("tr--pond-for-group");
    tabCell.id = "pond-for-group-" + iGroup;
    container.appendChild(table);
  }
}

function getUserFullName(id) {
  for (var i = 0; i < db_data_users.length; i++) {
    if (db_data_users[i]["id"] == id) {
      return (
        db_data_users[i]["first_name"] + " " + db_data_users[i]["last_name"]
      );
    }
  }
  return "Unknown Hunter";
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
  const route = base_uri + "/groupings/withdraw/" + e.currentTarget.group_id;

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
  // find the user_id of the current user via public id
  const public_id = decode_jwt(jwt_global, "user");
  var userId;
  for (var idxUser = 0; idxUser < db_data_users.length; idxUser++) {
    if (db_data_users[idxUser]["public_id"] == public_id) {
      userId = db_data_users[idxUser]["id"];
    }
  }

  // Create a new group for this user
  var object = {
    hunt_id: db_data_hunts["id"],
    slot1_id: userId,
    slot1_type: "member",
  };

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
}
