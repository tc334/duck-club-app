// functions, constants imported from other javascript files
import { base_uri } from "./constants.js";
import { callAPI, displayMessageToUser } from "./common_funcs.js";
import setup_landing from "./views/Setup/setup_landing.js";
import u_profile from "./views/Setup/members/u_profile.js";
import u_harvest from "./views/Setup/members/u_harvest.js";
import m_hunts from "./views/Setup/managers/m_hunts.js";
import m_add from "./views/Setup/managers/m_add.js";
import m_remove from "./views/Setup/managers/m_remove.js";
import m_groupings from "./views/Setup/managers/m_groupings.js";
import m_availability from "./views/Setup/managers/m_availability.js";
import o_properties from "./views/Setup/owners/o_properties.js";
import o_members from "./views/Setup/owners/o_members.js";
import o_birds from "./views/Setup/owners/o_birds.js";
import o_ponds from "./views/Setup/owners/o_ponds.js";
import o_guests from "./views/Setup/owners/o_guests.js";
import a_hunts from "./views/Setup/administrators/a_hunts.js";
import a_groupings from "./views/Setup/administrators/a_groupings.js";
import a_harvests from "./views/Setup/administrators/a_harvests.js";
import a_scheduler from "./views/Setup/administrators/a_scheduler.js";
import a_misc from "./views/Setup/administrators/a_misc.js";
import h_pre from "./views/Hunt/h_pre.js";
import h_no from "./views/Hunt/h_no.js";
import h_live from "./views/Hunt/h_live.js";
import live_hunt from "./views/live_hunt.js";
import s_dates from "./views/Stats/s_dates.js";
import s_hunters from "./views/Stats/s_hunters.js";
import s_ponds from "./views/Stats/s_ponds.js";
import s_birds from "./views/Stats/s_birds.js";
import s_club from "./views/Stats/s_club.js";
import s_hunt from "./views/Stats/s_hunt.js";
import m_scouting from "./views/Hunt/m_scouting.js";
import m_guests from "./views/Hunt/m_guests.js";
import u_scouting from "./views/Hunt/u_scouting.js";
import u_guests from "./views/Hunt/u_guests.js";
import u_invitations from "./views/Hunt/u_invitations.js";

// only do this once
const jwt = localStorage.getItem("token");
if (!jwt) {
  // If there isn't a JWT present, kick user back to login
  location.href = "login.html";
}

const goto_route = async (view, jwt) => {
  document.querySelector("#div-main").innerHTML = await view.getHtml();
  view.js(jwt);
};

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
      path: "#nav_hunt",
      view: live_hunt, // default only; branch below
    },
    {
      path: "#nav_stats",
      view: s_dates,
    },
    {
      path: "#m_scouting",
      view: m_scouting,
    },
    {
      path: "#m_guests",
      view: m_guests,
    },
    {
      path: "#u_scouting",
      view: u_scouting,
    },
    {
      path: "#u_guests",
      view: u_guests,
    },
    {
      path: "#u_invitations",
      view: u_invitations,
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
      path: "#m_remove",
      view: m_remove,
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
      path: "#u_harvest",
      view: u_harvest,
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
      path: "#o_guests",
      view: o_guests,
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
      path: "#a_harvests",
      view: a_harvests,
    },
    {
      path: "#a_scheduler",
      view: a_scheduler,
    },
    {
      path: "#a_misc",
      view: a_misc,
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
    {
      path: "#s_hunt",
      view: s_hunt,
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

  // for Hunts only, we have a branching view
  if (match.route.path == "#nav_hunt") {
    hunt_branch(jwt);
  } else {
    goto_route(new match.route.view(), jwt);
  }

  // This updates the view
  //const view = new match.route.view();
  //document.querySelector("#div-main").innerHTML = await view.getHtml();
  //view.js(jwt);
};

// call to router for initial page load
router();

// call to router for subsequent page loads
window.addEventListener("hashchange", function (e) {
  router();
});

// this is a special test used for the "Hunt" screen to route
// the page to either:
// signup-open, signup-closed, draw-complete: pre-hunt
// hunt-open: live-hunt
// else: no-hunt
function hunt_branch(jwt) {
  const route = base_uri + "/hunts/active";
  callAPI(
    jwt,
    route,
    "GET",
    null,
    (response_full_json) => {
      if (response_full_json["hunts"]) {
        const hunts_dict = response_full_json["hunts"];
        // logic
        if (hunts_dict.length == 1) {
          if (
            hunts_dict[0]["status"] == "signup_open" ||
            hunts_dict[0]["status"] == "signup_closed" ||
            hunts_dict[0]["status"] == "draw_complete"
          ) {
            goto_route(new h_pre(), jwt);
          } else if (hunts_dict[0]["status"] == "hunt_open") {
            goto_route(new h_live(), jwt);
          } else {
            goto_route(new h_no(), jwt);
          }
        } else {
          // this is an error condition. there should never be more than 1 hunt active
          goto_route(new h_no(), jwt);
        }
      } else {
        //console.log(data);
      }
    },
    displayMessageToUser
  );
}
