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
} from "../common_funcs.js";

const subroute = "birds";
const singular = "bird";
const plural = "birds";
// table sorting functions
const column_id_list = [
  {
    id: "col-name",
    is_numeric: false,
  },
  {
    id: "col-count",
    is_numeric: true,
  },
  {
    id: "col-pct",
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
          <div>
            <input type="date" class="inp-date-filter" value="2022-03-01" name="date-start" id="date-start">
            <label for="date-start">start</label>
          </div>
          <div>
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
            <th id="col-name">name</th>
            <th id="col-count">count</th>
            <th id="col-pct">%</th>
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
          //console.log(data["stats"]);
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
    tabCell.innerHTML = db_data[i]["name"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = db_data[i]["count"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = (db_data[i]["pct"] * 100).toFixed(0);
  }
}
