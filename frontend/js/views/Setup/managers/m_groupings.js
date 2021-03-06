import AbstractView from "../../AbstractView.js";
import { base_uri } from "../../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  dateConverter,
  decode_jwt,
  populate_aside,
} from "../../../common_funcs.js";

var jwt_global;
var db_data_groupings;
var db_data_users;
var db_data_ponds;
var db_data_hunts;
var group_index_merge_1;
const subroute = "groupings";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">groupings</h1>
    <div class="hunt-identifier" id="hunt-identifier"></div>
    <div id="tables-container" class="table-overflow-wrapper"></div>
    <div id="groupings-modal" class="modal">
      <div class="modal-content">
        <span class="close">&times;</span>
        <div class="modal-message"></div>
        <select class="modal-select" id="groupings-modal-select">
          <option>-</option>
        </select>
      </div>
    </div>
    `;
  }

  js(jwt) {
    // this variable is copied into the higher namespace so I can get it
    // into the delete function
    jwt_global = jwt;

    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside(user_level);

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
          writeTopMessage(db_data_hunts["hunt_date"], db_data_hunts["status"]);
          populateTables();
          selectCurrentPondAssignments();
          if (db_data_hunts["status"] == "signup_closed")
            addCloseDrawBtn(db_data_hunts["id"]);
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // get the modal
    var modal = document.getElementById("groupings-modal");

    // get the span element that closes the modal
    var span = document.getElementsByClassName("close")[0];

    // get the select inside the modal
    var select = document.getElementById("groupings-modal-select");

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

    // When the user selects an item in the select, close the modal
    // and call the DB to perfrm the merge
    select.addEventListener("change", () => {
      // close the modal
      modal.style.display = "none";

      // make sure the user didn't just try to merge a group with itself
      const group_id_merge_1 = db_data_groupings[group_index_merge_1]["id"];
      const group_id_merge_2 = select.value;

      if (group_id_merge_1 == group_id_merge_2) {
        localStorage.setItem(
          "previous_action_message",
          "Merge failed: both group #s were the same"
        );
        window.scrollTo(0, 0);
        location.reload();
      }

      const route =
        base_uri +
        "/groupings/merge/" +
        group_id_merge_1 +
        "/" +
        group_id_merge_2;

      callAPI(
        jwt,
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
    });
  }
}

function populateTables() {
  var container = document.getElementById("tables-container");
  const column_headings = ["#", "hunters", "pond", "actions"];
  var select = document.getElementById("groupings-modal-select");

  for (var iGroup = 0; iGroup < db_data_groupings.length; iGroup++) {
    // take this opportunity to populate the modal too
    var option_new = document.createElement("option");
    option_new.value = db_data_groupings[iGroup]["id"];
    option_new.className = "opt-group-merge2";
    option_new.innerHTML = iGroup + 1;
    select.appendChild(option_new);

    // create a table for each grouping
    var table = document.createElement("table");

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
    var pond_select = document.createElement("select");
    pond_select.idxGroup = iGroup;
    pond_select.id = "sel-pond-group-" + iGroup;
    pond_select.className = "sel-pond-group";
    populatePondList(pond_select);
    pond_select.addEventListener("change", updatePond);
    tabCell.appendChild(pond_select);

    // Actions
    var tabCell = tr.insertCell(-1);

    // Merge button
    var btn_merge = document.createElement("button");
    btn_merge.index = iGroup;
    btn_merge.innerHTML = "Merge";
    btn_merge.classList.add("btn--action", "btn--groupings-table");
    btn_merge.addEventListener("click", executeMerge);
    tabCell.appendChild(btn_merge);

    // Split button
    var btn_split = document.createElement("button");
    btn_split.index = iGroup;
    btn_split.innerHTML = "Split";
    btn_split.classList.add("btn--action", "btn--groupings-table");
    btn_split.addEventListener("click", splitGroup);
    tabCell.appendChild(btn_split);

    // Del button
    var btn_delete = document.createElement("button");
    btn_delete.index = iGroup;
    btn_delete.innerHTML = "Del";
    btn_delete.classList.add("btn--action", "btn--groupings-table");
    btn_delete.addEventListener("click", deleteGroup);
    tabCell.appendChild(btn_delete);

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

function splitGroup(e) {
  const group_index = e.currentTarget.index;
  const group_id = db_data_groupings[group_index]["id"];
  const route = base_uri + "/" + subroute + "/breakup/" + group_id;

  if (
    window.confirm(
      "You are about to split up group " + (group_index + 1) + ". Are you sure?"
    )
  ) {
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
}

function deleteGroup(e) {
  const group_index = e.currentTarget.index;
  const group_id = db_data_groupings[group_index]["id"];
  const route = base_uri + "/" + subroute + "/" + group_id;

  if (
    window.confirm(
      "You are about to delete group " + (group_index + 1) + ". Are you sure?"
    )
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

function executeMerge(e) {
  group_index_merge_1 = e.currentTarget.index;

  // update the message that the user will see in the modal
  document.getElementsByClassName("modal-message")[0].innerHTML =
    "Select a group # to merge with #" + (group_index_merge_1 + 1);

  // remove group 1 from the modal dropdown list
  enableAllOptions();
  var all = document.getElementsByClassName("opt-group-merge2");
  var one = all[group_index_merge_1];
  one.disabled = true;

  document.getElementById("groupings-modal").style.display = "block";
}

function enableAllOptions() {
  var options = document.getElementsByClassName("opt-group-merge2");
  for (var i = 0; i < options.length; i++) {
    options[i].disabled = false;
  }
}

function writeTopMessage(hunt_date, hunt_status) {
  var postMessage;
  if (hunt_status == "signup_open") postMessage = "Signup is still OPEN";
  else if (hunt_status == "signup_closed") postMessage = "Signup is CLOSED";
  else if (hunt_status == "draw_complete")
    postMessage = "Draw has been completed.";
  document.getElementById("hunt-identifier").innerHTML =
    "Groups for " + dateConverter(hunt_date, true) + " hunt. " + postMessage;
}

function populatePondList(select) {
  // start with a blank element
  var option_new = document.createElement("option");
  option_new.className = "opt-pond";
  option_new.innerHTML = "-";
  select.appendChild(option_new);
  for (var idxPond = 0; idxPond < db_data_ponds.length; idxPond++) {
    var option_new = document.createElement("option");
    option_new.value = db_data_ponds[idxPond]["id"];
    option_new.className = "opt-pond";
    option_new.innerHTML = db_data_ponds[idxPond]["name"];
    select.appendChild(option_new);
  }
}

function selectCurrentPondAssignments() {
  for (var idxGroup = 0; idxGroup < db_data_groupings.length; idxGroup++) {
    if (db_data_groupings[idxGroup]["pond_id"] != null) {
      var select = document.getElementById("sel-pond-group-" + idxGroup);
      select.value = db_data_groupings[idxGroup]["pond_id"];
    }
  }
}

function updatePond(e) {
  if (db_data_hunts["status"] == "signup_open") {
    // you aren't allowed to modify ponds in this state
    localStorage.setItem(
      "previous_action_message",
      "Action failed: Pond selections cannot be modified until signup is closed"
    );
    window.scrollTo(0, 0);
    location.reload();
  } else {
    const idxGroup = e.currentTarget.idxGroup;
    var select = document.getElementById("sel-pond-group-" + idxGroup);
    const pond_id = select.value;
    const group_id = db_data_groupings[idxGroup]["id"];

    const route = base_uri + "/groupings/" + group_id;

    const json = {
      id: group_id,
      pond_id: pond_id,
    };

    callAPI(
      jwt_global,
      route,
      "PUT",
      JSON.stringify(json),
      (data) => {
        localStorage.setItem("previous_action_message", data["message"]);
        window.scrollTo(0, 0);
        location.reload();
      },
      displayMessageToUser
    );
  }
}

function addCloseDrawBtn(hunt_id) {
  var div = document.getElementById("div-main");

  var btn_close = document.createElement("button");
  btn_close.index = hunt_id;
  btn_close.innerHTML = "Progress Hunt to 'Draw Complete'";
  btn_close.classList.add("btn--form");
  btn_close.addEventListener("click", closeDraw);

  div.appendChild(btn_close);
}

function closeDraw(e) {
  const hunt_id = e.currentTarget.index;
  const route = base_uri + "/hunts/" + hunt_id;

  const json = {
    id: hunt_id,
    status: "draw_complete",
  };

  if (window.confirm("You are about to close the draw. Are you sure?")) {
    callAPI(
      jwt_global,
      route,
      "PUT",
      JSON.stringify(json),
      (data) => {
        localStorage.setItem("previous_action_message", data["message"]);
        window.scrollTo(0, 0);
        location.reload();
      },
      displayMessageToUser
    );
  }
}
