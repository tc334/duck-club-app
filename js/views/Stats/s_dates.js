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
  dateConverter_http,
} from "../../common_funcs.js";

// table sorting functions
const column_id_list = [
  {
    id: "col-pond",
    is_numeric: false,
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
    return `<div class="reload-message"></div>
    <h2 class="heading-secondary">Filters</h2>
    <form id="form-filter">
      <div class="filter-container">
        <section class="filter-date-exact">
          <label for="select-date">Choose A Hunt Date</label>
          <select id="select-date" name="hunt_id">
          </select>
        </section>
      </div>  
      <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
    </form>
    <h1 class="heading-primary" id="stats-heading"></h1>
    <p class="sort-helper">Click on any header to sort table</p>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <thead>
          <tr>
            <th id="col-pond">name</th>
            <th id="col-ducks">ducks</th>
            <th id="col-non">non-ducks</th>
            <th id="col-total">total</th>
            <th id="col-ave">ave. ducks/hunter</th>
          </tr>
        </thead>
        <tbody id="tb-stats">
        </tbody>
      </table>
    </div>`;
  }

  js(jwt) {
    // check for reload message; if exists, display
    reloadMessage();

    populate_aside_stats();

    const myForm = document.getElementById("form-filter");
    populateDateList(jwt, myForm);

    // What do do on a submit
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();
      mySubmit(jwt, this);
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

// separating this function out allows me to call it automatically on page load
function mySubmit(jwt, myForm) {
  // Pull data from form and put it into the json format the DB wants
  const formData = new FormData(myForm); // myForm was this

  var object = {};
  formData.forEach((value, key) => (object[key] = value));

  // API route for this stats page
  const route = base_uri + "/groupings/harvest_summary/" + object["hunt_id"];

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      //console.log(data["data"]["groups"]);
      populateTable(data["data"]["groups"]);
    },
    displayMessageToUser
  );
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
    tabCell.innerHTML = round(db_data[i]["num_ducks"], 1).toFixed(0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(db_data[i]["num_nonducks"], 1).toFixed(0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = round(
      db_data[i]["num_ducks"] + db_data[i]["num_nonducks"],
      0
    ).toFixed(0);

    var tabCell = tr.insertCell(-1);
    tabCell.classList.add("cell-fixed-width");
    tabCell.style.textAlign = "right";
    tabCell.innerHTML = (
      db_data[i]["num_ducks"] / db_data[i]["num_hunters"]
    ).toFixed(1);
  }
}

function populateDateList(jwt, myForm) {
  // API route for this stats page
  const route = base_uri + "/hunts/dates";

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      //console.log(data["dates"]);
      populateDateList_aux(data["dates"]);
      if (data["dates"] && data["dates"].length > 0) {
        mySubmit(jwt, myForm);
      }
    },
    displayMessageToUser
  );
}

function populateDateList_aux(db_data) {
  const select_dates = document.getElementById("select-date");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = dateConverter_http(db_data[i]["hunt_date"]);
    new_opt.value = db_data[i]["id"];
    select_dates.appendChild(new_opt);
  }
}
