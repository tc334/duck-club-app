export function callAPI(jwt, route, method, body, func_success, func_fail) {
  let h = new Headers();
  h.append("Accept", "application/json");
  h.append("x-access-token", jwt);

  if (method == "POST" || method == "PUT") {
    h.append("Content-Type", "application/json");
  }

  fetch(route, {
    method: method,
    headers: h,
    body: body,
  })
    .then(async (response) => {
      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : null;

      if (!response.ok) {
        // There are some error codes we want to take specific actions against
        if (response.status == 401) {
          //Authentication failed. Sending you back to the login page
          location.href = "login.html";
          return null;
        } else if (response.status == 403) {
          const error = "You don't have permission for this action";
          func_fail(error);
          return Promise.reject(error);
        } else {
          // Generic error
          const error = "error " + response.status + ", " + data["message"];
          func_fail(error);
          return Promise.reject(error);
        }
      }

      // if you reached here, response is "ok"
      if (isJson) {
        func_success(data);
      }
    })
    .catch((err) => {
      console.log(err);
    });
}

export function decode_jwt(jwt_in, property = "level") {
  var tokens = jwt_in.split(".");
  const jwt_content = JSON.parse(atob(tokens[1]));
  return jwt_content[property];
}

// Populate the aside depending on user level
export function populate_aside(user_level) {
  // start by clearing the aside
  removeAllChildNodes(document.getElementById("aside-main"));

  // data
  const headings = ["member", "manager", "owner", "administrator"];

  const icons = {
    member: ["img/clock.png", "img/user.png"],
    manager: [
      "img/cog-wheel.png",
      "img/plus.png",
      "img/wrench.png",
      "img/traffic-signal.png",
      "img/edit.png",
    ],
    owner: [
      "img/people.png",
      "img/location.png",
      "img/drop.png",
      "img/bird.png",
    ],
    administrator: ["img/cog-wheel.png", "img/cog-wheel.png"],
  };

  const text = {
    member: ["pre hunt", "profile"],
    manager: [
      "manage hunt",
      "add hunter",
      "adjust groupings",
      "pond availability",
      "edit harvest",
    ],
    owner: ["members", "properties", "ponds", "birds"],
    administrator: ["hunts", "groupings"],
  };

  const links = {
    member: ["#u_pre", "#u_profile"],
    manager: [
      "#m_hunts",
      "#m_add",
      "#m_groupings",
      "#m_availability",
      "#m_harvest",
    ],
    owner: ["#o_members", "#o_properties", "#o_ponds", "#o_birds"],
    administrator: ["#a_hunts", "#a_groupings"],
  };

  const idx_in = headings.indexOf(user_level);

  for (var i = 0; i < headings.length; i++) {
    if (i <= idx_in) {
      populateOneLevel(
        headings[i],
        text[headings[i]],
        icons[headings[i]],
        links[headings[i]]
      );
    }
  }

  document.getElementById("aside-main").style.display = "block";
}

// Populate the alternate aside for the stats menu
export function populate_aside_stats() {
  // start by clearing the aside
  removeAllChildNodes(document.getElementById("aside-main"));

  // data
  const headings = ["stats"];

  const icons = {
    stats: ["img/user.png", "img/drop.png", "img/bird.png", "img/people.png"],
  };

  const text = {
    stats: ["by hunter", "by pond", "by bird", "club"],
  };

  const links = {
    stats: ["#s_hunters", "#s_hunters", "#s_hunters", "#s_hunters"],
  };

  const idx_in = 1;

  for (var i = 0; i < headings.length; i++) {
    if (i <= idx_in) {
      populateOneLevel(
        headings[i],
        text[headings[i]],
        icons[headings[i]],
        links[headings[i]]
      );
    }
  }

  document.getElementById("aside-main").style.display = "block";
}

function populateOneLevel(heading, text, images, links) {
  var aside = document.getElementById("aside-main");

  // heading
  var div = document.createElement("div");
  div.className += "aside-heading";
  div.innerHTML = heading;
  aside.appendChild(div);

  // unordered list
  var ul = document.createElement("ul");
  ul.className = "aside-list";

  // links
  for (var i = 0; i < text.length; i++) {
    // icon image
    var img = document.createElement("img");
    img.className = "aside-icon";
    img.src = images[i];

    // navigation text
    div = document.createElement("div");
    div.className = "aside-item-text";
    div.innerHTML = text[i];

    // anchor
    var a = document.createElement("a");
    a.href = links[i];
    a.appendChild(img);
    a.appendChild(div);

    // list item
    var li = document.createElement("li");
    li.appendChild(a);

    ul.appendChild(li);
  }

  aside.appendChild(ul);
}

export function removeAllChildNodes(parent) {
  while (parent.firstChild) {
    parent.removeChild(parent.firstChild);
  }
}

export function displayMessageToUser(msg) {
  document.querySelector(".reload-message").innerHTML = msg;
}

export function reloadMessage() {
  // check for reload message; if exists, display
  const new_msg = localStorage.getItem("previous_action_message");
  if (new_msg) {
    document.querySelector(".reload-message").innerHTML = new_msg;
    localStorage.removeItem("previous_action_message");
  }
}

export const formatDate = (date) => {
  let d = new Date(date);
  let month = (d.getMonth() + 1).toString();
  let day = d.getDate().toString();
  let year = d.getFullYear();
  if (month.length < 2) {
    month = "0" + month;
  }
  if (day.length < 2) {
    day = "0" + day;
  }
  return [year, month, day].join("-");
};

export function dateConverter(from_db, month_first = false) {
  // converts HTTP date to year, month, day w/o regard to timezone
  const myArray = from_db.split(" ");
  const year = myArray[3];
  const day = myArray[1];
  const month_long = myArray[2];
  if (month_first) {
    return monthConverter(month_long) + "/" + day + "/" + year;
  } else {
    return year + "-" + monthConverter(month_long) + "-" + day;
  }
}

export function monthConverter(month_long) {
  if (month_long == "Jan") return "01";
  else if (month_long == "Feb") return "02";
  else if (month_long == "Mar") return "03";
  else if (month_long == "Apr") return "04";
  else if (month_long == "May") return "05";
  else if (month_long == "Jun") return "06";
  else if (month_long == "Jul") return "07";
  else if (month_long == "Aug") return "08";
  else if (month_long == "Sep") return "09";
  else if (month_long == "Oct") return "10";
  else if (month_long == "Nov") return "11";
  else if (month_long == "Dec") return "12";
  else return "00";
}

export function sortIndexes(test) {
  var test_with_index = [];
  test.forEach((element, index) => test_with_index.push([element, index]));
  test_with_index.sort(function (left, right) {
    return left[0] > right[0] ? -1 : 1;
  });
  var indexes = [];
  //test = [];
  for (var j in test_with_index) {
    //test.push(test_with_index[j][0]);
    indexes.push(test_with_index[j][1]);
  }
  return indexes;
}

export function round(value, precision) {
  var multiplier = Math.pow(10, precision || 0);
  return Math.round(value * multiplier) / multiplier;
}
