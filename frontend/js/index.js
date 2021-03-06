// functions, constants imported from other javascript files
//import { decode_jwt, populate_aside } from "./common_funcs.js";
import setup_landing from "./views/Setup/setup_landing.js";
import u_pre from "./views/Setup/members/u_pre.js";
import u_profile from "./views/Setup/members/u_profile.js";
import m_hunts from "./views/Setup/managers/m_hunts.js";
import m_add from "./views/Setup/managers/m_add.js";
import m_groupings from "./views/Setup/managers/m_groupings.js";
import m_availability from "./views/Setup/managers/m_availability.js";
import m_harvest from "./views/Setup/managers/m_harvest.js";
import o_properties from "./views/Setup/owners/o_properties.js";
import o_members from "./views/Setup/owners/o_members.js";
import o_birds from "./views/Setup/owners/o_birds.js";
import o_ponds from "./views/Setup/owners/o_ponds.js";
import a_hunts from "./views/Setup/administrators/a_hunts.js";
import a_groupings from "./views/Setup/administrators/a_groupings.js";
import live_hunt from "./views/live_hunt.js";
import s_dates from "./views/Stats/s_dates.js";
import s_hunters from "./views/Stats/s_hunters.js";
import s_ponds from "./views/Stats/s_ponds.js";
import s_birds from "./views/Stats/s_birds.js";
import s_club from "./views/Stats/s_club.js";

// only do this once
const jwt = localStorage.getItem("token");
if (!jwt) {
  // If there isn't a JWT present, kick user back to login
  location.href = "login.html";
}

const router = async () => {
  const routes = [
    {
      path: "/",
      view: setup_landing,
    },
    {
      path: "#nav_setup",
      view: setup_landing,
    },
    {
      path: "#nav_live",
      view: live_hunt,
    },
    {
      path: "#nav_stats",
      view: s_dates,
    },
    {
      path: "#u_pre",
      view: u_pre,
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
      path: "#m_groupings",
      view: m_groupings,
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
    {
      path: "#a_hunts",
      view: a_hunts,
    },
    {
      path: "#a_groupings",
      view: a_groupings,
    },
    {
      path: "#s_dates",
      view: s_dates,
    },
    {
      path: "#s_hunters",
      view: s_hunters,
    },
    {
      path: "#s_ponds",
      view: s_ponds,
    },
    {
      path: "#s_birds",
      view: s_birds,
    },
    {
      path: "#s_club",
      view: s_club,
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
