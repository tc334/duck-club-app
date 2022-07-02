import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside_stats,
  round,
  removeAllChildNodes,
  sortTable,
  dateConverter,
} from "../common_funcs.js";

const subroute = "club";
const singular = "club";
const plural = "club";
// table sorting functions
const column_id_list = [
  {
    id: "col-date",
    is_numeric: false,
  },
  {
    id: "col-groups",
    is_numeric: true,
  },
  {
    id: "col-hunters",
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
  {
    id: "col-limit",
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
              <input type="radio" name="filter-member" id="radio-just-me" value="just-me" disabled>
              <label for="radio-just-me">just me</label>
            </li>
          </ul>
        </section>
      </div>  
      <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
    </form>
    <h1 class="heading-primary" id="stats-heading">` +
      singular +
      ` stats</h1>
    <p class="sort-helper">Click on any header to sort table</p>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <thead>
          <tr>
            <th class="rotate" id="col-date"><div class="rotate">date</div></th>
            <th class="rotate" id="col-groups"><div class="rotate">groups</div></th>
            <th class="rotate" id="col-hunters"><div class="rotate">hunters</div></th>
            <th class="rotate" id="col-ducks"><div class="rotate">ducks</div></th>
            <th class="rotate" id="col-non"><div class="rotate">non-ducks</div></th>
            <th class="rotate" id="col-total"><div class="rotate">total</div></th>
            <th class="rotate" id="col-ave"><div class="rotate">ave. ducks</div></th>
            <th class="rotate" id="col-limit"><div class="rotate">limit %</div></th>
          </tr>
        </thead>
        <tbody id="tb-stats">
        </tbody>
      </table>
    </div>`
    );
  }

  js(jwt) {
    // check for reload message; if exists, display
    reloadMessage();

    populate_aside_stats();

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
          console.log(data["stats"]);
          populateTable(data["stats"]);
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
    tabCell.innerHTML = dateConverter(db_data[i]["date"]);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = db_data[i]["num_groups"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = db_data[i]["num_hunters"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["num_ducks"], 0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["non_ducks"], 0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(
      db_data[i]["num_ducks"] + db_data[i]["non_ducks"],
      0
    );

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = (
      db_data[i]["num_ducks"] / db_data[i]["num_hunters"]
    ).toFixed(1);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = (
      (db_data[i]["limits"] / db_data[i]["num_groups"]) *
      100
    ).toFixed(0);
  }
}
