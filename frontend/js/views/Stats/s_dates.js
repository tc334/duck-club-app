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

var jwt_global;
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
  {
    id: "col-detail",
    is_numeric: false,
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
            <th id="col-non">non-dks.</th>
            <th id="col-total">total</th>
            <th id="col-ave">ave. dks./hntr.</th>
            <th id="col-detail">detail</th>
          </tr>
        </thead>
        <tbody id="tb-stats">
        </tbody>
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
  </div>`;
  }

  js(jwt) {
    jwt_global = jwt;

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

    var tabCell = tr.insertCell(-1);
    // create a row for each grouping
    var btn_detail = document.createElement("button");
    btn_detail.classList.add("leaderboard-entry");
    btn_detail.group_id = db_data[i]["group_id"];
    btn_detail.addEventListener("click", selectGroup);
    btn_detail.innerHTML = "Click Here";
    btn_detail.classList.add("btn-detail");
    tabCell.appendChild(btn_detail);
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
        // members first, then guests
        var slot = 0;
        for (var i = 0; i < db_data["hunters"]["members"].length; i++) {
          slot += 1;
          var table_cell_name = document.getElementById("modal-hunter" + slot);
          table_cell_name.innerHTML = db_data["hunters"]["members"][i];
        }
        if (db_data["hunters"]["guests"].length > 0) {
          for (var i = 0; i < db_data["hunters"]["guests"].length; i++) {
            slot += 1;
            var table_cell_name = document.getElementById(
              "modal-hunter" + slot
            );
            table_cell_name.innerHTML = db_data["hunters"]["guests"][i];
          }
        }
        // clear names in the remaining blank slots
        while (slot < 4) {
          slot += 1;
          var table_cell_name = document.getElementById("modal-hunter" + slot);
          table_cell_name.innerHTML = "";
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
