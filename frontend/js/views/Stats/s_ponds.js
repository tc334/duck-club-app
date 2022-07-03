import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside_stats,
  round,
  removeAllChildNodes,
  sortTable,
  dateConverter,
} from "../../common_funcs.js";

const subroute = "ponds";
const singular = "pond";
const plural = "ponds";
// table sorting functions
const column_id_list = [
  {
    id: "col-name",
    is_numeric: false,
  },
  {
    id: "col-hunts",
    is_numeric: true,
  },
  {
    id: "col-ducks",
    is_numeric: true,
  },
  {
    id: "col-non",
    is_numeric: true,
  },
  {
    id: "col-total",
    is_numeric: true,
  },
  {
    id: "col-ave",
    is_numeric: true,
  },
];

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
        <section class="filter-date">
          <ul class="filter-list">
            <li>
              <input type="radio" name="filter-date" id="radio-current-season" value="current-season" checked>
              <label for="radio-current-season">current season</label>
            </li>
            <li>
              <input type="radio" name="filter-date" id="radio-all-records" value="all-records">
              <label for="radio-all-records">all records</label>
            </li>
            <li>
              <input type="radio" name="filter-date" id="radio-custom-date" value="custom-range">
              <label for="radio-custom-date">custom date range:</label>
            </li>
          </ul>
          <div class="custom-date">
            <input type="date" class="inp-date-filter" value="2022-03-01" name="date-start" id="date-start">
            <label for="date-start">start</label>
          </div>
          <div class="custom-date">
            <input type="date" class="inp-date-filter" value="2023-03-01" name="date-end" id="date-end">
            <label for="date-end">end</label>
          </div>
        </section>
        <section class="filter-member">
          <ul class="filter-list">
            <li>
              <input type="radio" name="filter-member" id="radio-whole-club" value="whole-club" checked>
              <label for="radio-whole-club">whole club</label>
            </li>
            <li>
              <input type="radio" name="filter-member" id="radio-just-me" value="just-me">
              <label for="radio-just-me">just me</label>
            </li>
          </ul>
        </section>
        <section class="filter-pond">
          <label for="select-pond">Pick One For Hunt History</label>
          <select id="select-pond" name="pond_id">
            <option value=-1>--select pond--</option>
          </select>
        </section>
      </div>  
      <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
    </form>
    <h1 class="heading-primary" id="stats-heading">stats by ` +
      singular +
      `</h1>
    <p class="sort-helper">Click on any header to sort table</p>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <thead>
          <tr>
            <th id="col-name">name</th>
            <th id="col-hunts">hunts</th>
            <th id="col-ducks">ducks</th>
            <th id="col-non">non-ducks</th>
            <th id="col-total">total</th>
            <th id="col-ave">ave. ducks/hunter</th>
          </tr>
        </thead>
        <tbody id="tb-stats">
        </tbody>
      </table>
    </div>
    <h1 class="heading-primary" id="stats-heading-2">
      hunt history of TBD
    </h1>
    <p class="sort-helper">Click on any header to sort table</p>
    <div class="table-overflow-wrapper">
      <table id="data-table-2">
        <thead>
          <tr>
            <th id="col-date">date</th>
            <th id="col-day">day</th>
            <th id="col-ducks">ducks</th>
            <th id="col-ave">ave. ducks/hunter</th>
          </tr>
        </thead>
        <tbody id="tb-stats-2">
        </tbody>
      </table>
    </div>`
    );
  }

  js(jwt) {
    // check for reload message; if exists, display
    reloadMessage();

    populate_aside_stats();

    populatePondList(jwt);

    // What do do on a submit
    const myForm = document.getElementById("form-filter");
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));

      // API route for this stats page
      const route =
        base_uri +
        "/stats/" +
        subroute +
        "?" +
        new URLSearchParams(object).toString();

      callAPI(
        jwt,
        route,
        "GET",
        null,
        (data) => {
          //console.log(data["stats"]);
          populateTable(data["stats"]);
          if (data["hunt_history"]) {
            prePopTab2();
            populateTable2(data["hunt_history"]);
          }
        },
        displayMessageToUser
      );
    });

    // table sorting functions
    for (var i = 0; i < column_id_list.length; i++) {
      var temp = document.getElementById(column_id_list[i]["id"]);
      temp.column_index = i;
      temp.is_numeric = column_id_list[i]["is_numeric"];
      temp.addEventListener("click", sortTable);
    }
  }
}

function populateTable(db_data) {
  var table = document.getElementById("tb-stats");
  removeAllChildNodes(table);

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["pond_name"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = db_data[i]["num_hunts"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["num_ducks"], 1).toFixed(0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["non_ducks"], 1).toFixed(0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(
      db_data[i]["num_ducks"] + db_data[i]["non_ducks"],
      0
    ).toFixed(0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = db_data[i]["ave_ducks"].toFixed(1);
  }
}

function prePopTab2() {
  // this function gets called regardless of presence of "hunt_history"
  var heading = document.getElementById("stats-heading-2");
  const select_ponds = document.getElementById("select-pond");
  heading.innerHTML =
    "Hunt History of " + select_ponds.options[select_ponds.value].text;

  var table = document.getElementById("tb-stats-2");
  removeAllChildNodes(table);
}

function populateTable2(db_data) {
  var table = document.getElementById("tb-stats-2");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = dateConverter(db_data[i]["date"]);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["date"].split(",")[0];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["num_ducks"], 1).toFixed(0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = db_data[i]["ave_ducks"].toFixed(1);
  }
}

function populatePondList(jwt) {
  // API route for this stats page
  const route = base_uri + "/ponds";

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      populatePondList_aux(data["ponds"]);
    },
    displayMessageToUser
  );
}

function populatePondList_aux(db_data) {
  const select_ponds = document.getElementById("select-pond");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = db_data[i]["name"];
    new_opt.value = db_data[i]["id"];
    select_ponds.appendChild(new_opt);
  }
}
