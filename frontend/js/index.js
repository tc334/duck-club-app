// functions, constants imported from other javascript files
import { decode_jwt, populate_aside } from "./common_funcs.js";
import u_profile from "./views/u_profile.js";
import m_hunts from "./views/m_hunts.js";
import m_add from "./views/m_add.js";
import m_availability from "./views/m_availability.js";
import m_harvest from "./views/m_harvest.js";
import o_properties from "./views/o_properties.js";
import o_members from "./views/o_members.js";
import o_birds from "./views/o_birds.js";
import o_ponds from "./views/o_ponds.js";

// only do this once
const jwt = localStorage.getItem("token");
if (!jwt) {
  // If there isn't a JWT present, kick user back to login
  location.href = "login.html";
}
const user_level = decode_jwt(jwt);
populate_aside(user_level);

const router = async () => {
  const routes = [
    {
      path: "/",
      view: () => console.log("Viewing home"),
    },
    {
      path: "#u_profile",
      view: u_profile,
    },
    {
      path: "#m_hunts",
      view: m_hunts,
    },
    {
      path: "#m_add",
      view: m_add,
    },
    {
      path: "#m_availability",
      view: m_availability,
    },
    {
      path: "#m_harvest",
      view: m_harvest,
    },
    {
      path: "#o_members",
      view: o_members,
    },
    {
      path: "#o_properties",
      view: o_properties,
    },
    {
      path: "#o_ponds",
      view: o_ponds,
    },
    {
      path: "#o_birds",
      view: o_birds,
    },
  ];

  // Test each route for potential match
  const potentialMatches = routes.map((route) => {
    return {
      route: route,
      isMatch: location.hash === route.path,
    };
  });

  let match = potentialMatches.find((potentialMatch) => potentialMatch.isMatch);

  // replace this my own custom 404
  if (!match) {
    match = {
      route: routes[0],
      isMatch: true,
    };
  }

  // This updates the view
  console.log("Zulu: " + match["route"]["path"]);
  const view = new match.route.view();
  document.querySelector("#div-main").innerHTML = await view.getHtml();
  view.js(jwt);
};

// call to router for initial page load
router();

// call to router for subsequent page loads
window.addEventListener("hashchange", function (e) {
  router();
});
