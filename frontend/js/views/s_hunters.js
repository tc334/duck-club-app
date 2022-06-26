import AbstractView from "./AbstractView.js";
import { base_uri } from "../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside_stats,
  round,
  removeAllChildNodes,
} from "../common_funcs.js";

const subroute = "hunters";
const singular = "hunter";
const plural = "hunters";

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
      <button class="btn--form btn--cntr" id="btn-filter-refresh">Refresh</button>
    </form>
    <h1 class="heading-primary">` +
      singular +
      ` stats</h1>
    <table id="data-table">
      <thead>
        <tr>
          <th>name</th>
          <th>hunts</th>
          <th>ducks</th>
          <th>non-ducks</th>
          <th>total</th>
          <th>ave. ducks</th>
        </tr>
      </thead>
      <tbody id="tb-stats">
      </tbody>
    </table>`
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
  }
}

function populateTable(db_data) {
  var table = document.getElementById("tb-stats");
  removeAllChildNodes(table);

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML =
      db_data[i]["first_name"] + " " + db_data[i]["last_name"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = db_data[i]["hunts"];

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["ducks"], 1).toFixed(1);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["non_ducks"], 1).toFixed(1);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(
      db_data[i]["ducks"] + db_data[i]["non_ducks"],
      1
    ).toFixed(1);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(
      db_data[i]["ducks"] / db_data[i]["hunts"],
      2
    ).toFixed(2);
  }
}
