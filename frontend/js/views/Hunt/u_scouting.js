import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  sortTable,
  decode_jwt,
  populate_aside_hunt,
} from "../../common_funcs.js";

var jwt_global;
var db_data;
var db_data_ponds;
const subroute = "scouts";

// table sorting functions
const column_id_list = [
  {
    id: "col-id",
    is_numeric: false,
  },
  {
    id: "col-property",
    is_numeric: false,
  },
  {
    id: "col-pond",
    is_numeric: false,
  },
  {
    id: "col-count",
    is_numeric: true,
  },
  {
    id: "col-notes",
    is_numeric: false,
  },
  {
    id: "col-scout",
    is_numeric: false,
  },
];

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">scouting reports</h1>
    <p class="sort-helper">Click on any header to sort table</p>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <thead>
          <tr>
            <th id="col-id">id</th>
            <th id="col-property">property</th>
            <th id="col-pond">pond</th>
            <th id="col-count">count</th>
            <th id="col-notes">notes</th>
            <th id="col-scout">scout</th>
          </tr>
        </thead>
      </table>
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

    // First step is to pull data from DB
    const route = base_uri + "/" + subroute;
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        if (response_full_json["data"]) {
          db_data = response_full_json["data"];
          populateTable(db_data);
        } else {
          //console.log(data);
        }
      },
      displayMessageToUser
    );

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
  var table = document.getElementById("data-table");

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["id"].slice(0, 3);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["property"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["pond"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["count"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["notes"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["scout"];
  }
}
