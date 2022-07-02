import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  dateConverter,
  sortIndexes,
  removeAllChildNodes,
  round,
  menuSwitcher,
} from "../common_funcs.js";

var jwt_global;
var group_limits = [];
const subroute = "groupings";

document.getElementById("main").classList.remove("menu-open");
document
  .getElementById("btn-aside-menu")
  .addEventListener("click", menuSwitcher);

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <div id="leaderboard-container">
      <h1 class="heading-primary">leaderboard</h1>
      <header id="leaderboard-header">
        <span>Pond</span>
        <span>Ducks</span>
        <span>Limit</span>
        <span>Other</span>
        <span>Updated</span>
      </header>
    </div>
    <div id="hunt-summary">
      <h1 class="heading-primary">club summary</h1>
      <table class="leaderboard-table">
        <tr>
          <th colspan="2" id="hunt-summary-date"></th>
        </tr>
        <tr>
          <th>total birds</th>
          <td id="hunt-summary-total"></td>
        </tr>
        <tr>
          <th>duck average</th>
          <td id="hunt-summary-duckave"></td>
        </tr>
        <tr>
          <th>group limits</th>
          <td id="hunt-summary-grouplimits"></td>
        </tr>
      </table>
    </div>
    <div id="harvest-modal" class="modal">
      <div class="modal-content">
        <span class="close">&times;</span>
        <h2 id="modal-group-heading"></h2>
        <table class="leaderboard-table" id="modal-group-table">
          <tr>
            <th>Pond</th>
            <td id="modal-pond"></td>
          </tr>
          <tr>
            <th>Hunter 1</thclass=>
            <td id="modal-hunter1"></td>
          </tr>
          <tr>
            <th>Hunter 2</thlass=>
            <td id="modal-hunter2"></td>
          </tr>
          <tr>
            <th>Hunter 3</thclass=>
            <td id="modal-hunter3"></td>
          </tr>
          <tr>
            <th>Hunter 4</thclass=>
            <td id="modal-hunter4"></td>
          </tr>
        </table>
        <h1 class="heading-primary">Harvest Detail</h1>
        <div id="harvest-detail"></div>
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

    // clear the aside
    var aside = document.getElementById("aside-content");
    aside.innerHTML = "";

    // First step is to pull data from DB
    const route = base_uri + "/groupings/harvest_summary";
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          const pct_complete = populateSummaryTable(response_full_json["data"]);
          populateLeaderboard(
            response_full_json["data"]["groups"],
            pct_complete
          );
          if (response_full_json["data"]["this_user"]) {
            // populate aside
            populateAside(response_full_json["data"]["this_user"]);
          } else {
            // hide the aside
            aside.style.display = "none";
          }
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

    // get the modal
    var modal = document.getElementById("harvest-modal");

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

function populateSummaryTable(db_data) {
  document.getElementById("hunt-summary-date").innerHTML = dateConverter(
    db_data["hunt_date"],
    true
  );

  const num_groups = db_data["groups"].length;
  var pct_complete = [];
  var num_birds_total = 0;
  var num_ducks_total = 0;
  var num_hunters_total = 0;
  var num_limits = 0;
  for (var iGroup = 0; iGroup < num_groups; iGroup++) {
    num_hunters_total += db_data["groups"][iGroup]["num_hunters"];
    num_ducks_total += db_data["groups"][iGroup]["num_ducks"];
    num_birds_total += db_data["groups"][iGroup]["num_ducks"];
    if (
      db_data["groups"][iGroup]["num_ducks"] >=
      6 * db_data["groups"][iGroup]["num_hunters"]
    ) {
      num_limits += 1;
      group_limits.push(iGroup);
    }
    pct_complete.push(
      db_data["groups"][iGroup]["num_ducks"] /
        (6 * db_data["groups"][iGroup]["num_hunters"])
    );
  }

  document.getElementById("hunt-summary-total").innerHTML = num_birds_total;
  document.getElementById("hunt-summary-duckave").innerHTML = round(
    num_ducks_total / num_hunters_total,
    1
  ).toFixed(1);
  document.getElementById("hunt-summary-grouplimits").innerHTML =
    num_limits +
    "/" +
    num_groups +
    " (" +
    round((num_limits / num_groups) * 100, 0) +
    "%)";

  return pct_complete;
}

function populateLeaderboard(groups, pct_complete) {
  var container = document.getElementById("leaderboard-container");

  const sorted_indexes = sortIndexes(pct_complete);

  for (var i = 0; i < sorted_indexes.length; i++) {
    const iGroup = sorted_indexes[i];

    // create a row for each grouping
    var btn_thisgroup = document.createElement("button");
    btn_thisgroup.classList.add("leaderboard-entry");
    btn_thisgroup.group_id = groups[iGroup]["group_id"];
    btn_thisgroup.addEventListener("click", selectGroup);

    // Pond name
    // There is an extra container here to support the "Limit" indicator
    var pond_name_container = document.createElement("span");
    pond_name_container.classList.add("pond-name-container");
    var span_pond = document.createElement("span");
    span_pond.innerHTML = groups[iGroup]["pond_name"];
    span_pond.classList.add("leaderboard-span");
    span_pond.classList.add("pond-name");
    // if the group is at limit, turn on the after pseudo-element
    if (group_limits.includes(iGroup)) {
      var limit = document.createElement("span");
      limit.classList.add("limit");
      limit.innerHTML = "Limit";
      span_pond.appendChild(limit);
    }
    pond_name_container.appendChild(span_pond);
    btn_thisgroup.appendChild(pond_name_container);
    // # ducks harvested
    var span_duck_count = document.createElement("span");
    span_duck_count.innerHTML = groups[iGroup]["num_ducks"];
    span_duck_count.classList.add("leaderboard-span");
    span_duck_count.classList.add("leaderboard-duckcount");
    span_duck_count.classList.add("fixed-width-span");
    btn_thisgroup.appendChild(span_duck_count);

    // # max harvest
    var span_limit_count = document.createElement("span");
    span_limit_count.innerHTML = 6 * groups[iGroup]["num_hunters"];
    span_limit_count.classList.add("leaderboard-span");
    span_limit_count.classList.add("fixed-width-span");
    btn_thisgroup.appendChild(span_limit_count);

    // # non-ducks harvested
    var span_nonduck_count = document.createElement("span");
    span_nonduck_count.innerHTML = groups[iGroup]["num_nonducks"];
    span_nonduck_count.classList.add("leaderboard-span");
    span_nonduck_count.classList.add("fixed-width-span");
    btn_thisgroup.appendChild(span_nonduck_count);

    // # time of last update
    var span_time_of_last_update = document.createElement("span");
    span_time_of_last_update.innerHTML = groups[iGroup]["harvest_update_time"];
    span_time_of_last_update.classList.add("leaderboard-span");
    btn_thisgroup.appendChild(span_time_of_last_update);

    container.appendChild(btn_thisgroup);
  }
}

function populateAside(group_detail) {
  var aside = document.getElementById("aside-content");
  aside.group_id = group_detail["group_id"];

  var heading = document.createElement("h2");
  heading.innerHTML = "My Group's Harvest";
  heading.classList.add("heading-secondary");
  aside.appendChild(heading);

  // create a row for each harvest
  for (var i = 0; i < group_detail["harvests"].length; i++) {
    var div = document.createElement("div");
    div.classList.add("myharvest-row");

    var bird_name = document.createElement("span");
    bird_name.innerHTML = group_detail["harvests"][i]["bird_name"];
    bird_name.classList.add("myharvest-name");
    div.appendChild(bird_name);

    var count = document.createElement("input");
    count.type = "number";
    count.min = 0;
    count.max = 24;
    count.step = 1;
    count.value = group_detail["harvests"][i]["count"];
    count.original_value = group_detail["harvests"][i]["count"];
    count.classList.add("myharvest-count");
    count.classList.add("myharvest-count-old");
    count.bird_id = group_detail["harvests"][i]["bird_id"];
    div.appendChild(count);

    aside.appendChild(div);
  }

  div = document.createElement("div");
  div.classList.add("myharvest-row");
  div.id = "myharvest-newrow";

  var bird_list = document.createElement("select");
  bird_list.id = "myharvest-newname";
  var opt = document.createElement("option");
  opt.innerHTML = "Add New";
  opt.value = "";
  opt.bird_id = -1; // indicator to skip this when button pressed
  bird_list.appendChild(opt);
  for (var i = 0; i < group_detail["birds"].length; i++) {
    // check to see if group already has a harvest entry for this bird
    var found_duplicate = false;
    for (
      var iBirdsHarvested = 0;
      iBirdsHarvested < group_detail["harvests"].length;
      iBirdsHarvested++
    ) {
      if (
        group_detail["harvests"][iBirdsHarvested]["bird_id"] ==
        group_detail["birds"][i]["id"]
      ) {
        found_duplicate = true;
        break;
      }
    }
    if (!found_duplicate) {
      var opt = document.createElement("option");
      opt.value = group_detail["birds"][i]["id"];
      opt.innerHTML = group_detail["birds"][i]["name"];
      opt.bird_id = group_detail["birds"][i]["id"];
      bird_list.appendChild(opt);
    }
  }
  bird_list.value = "";
  div.appendChild(bird_list);

  var count = document.createElement("input");
  count.type = "number";
  count.min = 0;
  count.max = 24;
  count.step = 1;
  count.value = 0;
  count.id = "myharvest-count-new";
  count.classList.add("myharvest-count");
  //count.classList.add("myharvest-count-new");
  div.appendChild(count);

  aside.appendChild(div);

  var btn_update = document.createElement("button");
  btn_update.innerHTML = "Update";
  btn_update.classList.add("btn--form");
  btn_update.classList.add("btn--cntr");
  btn_update.addEventListener("click", updateMyGroup);
  aside.appendChild(btn_update);
}

function updateMyGroup() {
  // this is the parent element
  var aside = document.getElementById("aside-content");

  // setup the json that will be sent to the PUT command
  var json = {
    group_id: aside.group_id,
    count: [],
    bird_id: [],
  };

  // loop over existing birds
  var counts = aside.querySelectorAll(".myharvest-count-old");
  for (var i = 0; i < counts.length; i++) {
    const new_count = parseInt(counts[i].value);
    // only add to this list if the count has changed
    if (parseInt(counts[i].original_value) != new_count) {
      json["count"].push(new_count);
      json["bird_id"].push(counts[i].bird_id);
    }
  }

  // check to see if new bird has been selected & count > 0
  var bird_list = document.getElementById("myharvest-newname");
  const input_count = document.getElementById("myharvest-count-new");
  const count = parseInt(input_count.value);
  if (bird_list.value != "" && count > 0) {
    json["count"].push(count);
    json["bird_id"].push(parseInt(bird_list.value));
  }

  // now call the API to update the harvest
  const route = base_uri + "/harvests";

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

function selectGroup(e) {
  const group_id = e.currentTarget.group_id;

  // Get the harvest details from the DB
  const route = base_uri + "/groupings/harvest_detail/" + group_id;
  callAPI(
    jwt_global,
    route,
    "GET",
    null,
    (response_full_json) => {
      if (response_full_json["data"]) {
        const db_data = response_full_json["data"];

        // load the data into the modal
        document.getElementById("modal-pond").innerHTML = db_data["pond"];

        // group info
        for (var i = 0; i < 4; i++) {
          var table_cell_name = document.getElementById(
            "modal-hunter" + (i + 1)
          );
          if (i < db_data["hunters"].length) {
            table_cell_name.innerHTML =
              db_data["hunters"][i]["first_name"] +
              " " +
              db_data["hunters"][i]["last_name"];
          } else {
            table_cell_name.innerHTML = "";
          }
        }

        // group harvest
        var container = document.getElementById("harvest-detail");
        removeAllChildNodes(container);
        for (var i = 0; i < db_data["harvests"].length; i++) {
          var section = document.createElement("section");
          section.classList.add("section-harvest");

          var name = document.createElement("span");
          name.innerHTML = db_data["harvests"][i]["bird_name"];
          name.classList.add("harvest-detail-name");
          section.appendChild(name);

          var count = document.createElement("span");
          count.innerHTML = db_data["harvests"][i]["count"];
          count.classList.add("harvest-detail-count");
          section.appendChild(count);

          container.appendChild(section);
        }
        // turn the modal on
        document.getElementById("harvest-modal").style.display = "block";
      } else {
        //console.log(data);
      }
    },
    displayMessageToUser
  );
}
