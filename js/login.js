import { base_uri } from "./constants.js";
import { callAPI } from "./common_funcs.js";

const form_login = {
  email: document.querySelector("#inp-login-email"),
  password: document.querySelector("#inp-login-password"),
  submit: document.querySelector("#btn-login-submit"),
  reset: document.querySelector("#inp-login-reset"),
};

const form_signup = {
  first_name: document.querySelector("#inp-signup-firstname"),
  last_name: document.querySelector("#inp-signup-lastname"),
  email: document.querySelector("#inp-signup-email"),
  password: document.querySelector("#inp-signup-password"),
  combo: [
    document.querySelector("#inp-combo-1"),
    document.querySelector("#inp-combo-2"),
    document.querySelector("#inp-combo-3"),
    document.querySelector("#inp-combo-4"),
  ],
  submit: document.querySelector("#btn-signup-submit"),
  reset: document.querySelector("#inp-signup-reset"),
};

let button = form_login.submit.addEventListener("click", (e) => {
  e.preventDefault();

  const login = base_uri + "/login";

  let h = new Headers();
  h.append("Accept", "application/json");
  let encoded = window.btoa(
    form_login.email.value + ":" + form_login.password.value
  );
  let auth = "Basic " + encoded;
  h.append("Authorization", auth);

  fetch(login, {
    method: "GET",
    headers: h,
  })
    .then((response) => {
      if (!response.ok) {
        reportFail("div-login-response", "Login Failed!");
        return null;
      }
      return response.json();
    })
    .then((data) => {
      if (!(data == null)) {
        localStorage.setItem("token", data["token"]);
        location.href = "index.html";
      }
    })
    .catch((err) => {
      console.log(err);
    });
});

document.getElementById("btn-passwordreset").addEventListener("click", (e) => {
  let email = prompt(
    "Enter the email address associated with your account, and a password reset link will be sent to you."
  );
  if (email == null || email == "") {
    return;
  }

  const route = base_uri + "/password_reset_request";
  const method = "POST";
  const body = JSON.stringify({
    email: email,
  });

  callAPI(
    null,
    route,
    method,
    body,
    (data) => {
      console.log("Submit appears to have succeeded");
    },
    (data) => {
      reportFail("div-signup-response", data);
    }
  );
});

let signup = form_signup.submit.addEventListener("click", (e) => {
  e.preventDefault();

  const route = base_uri + "/signup";
  const method = "POST";
  const body = JSON.stringify({
    first_name: form_signup.first_name.value,
    last_name: form_signup.last_name.value,
    email: form_signup.email.value,
    password: form_signup.password.value,
    combo:
      form_signup.combo[0].value +
      form_signup.combo[1].value +
      form_signup.combo[2].value +
      form_signup.combo[3].value,
  });
  // disable the user from pressing the sign-up button again until the server responds to this click
  document.getElementById("btn-signup-submit").disabled = true;
  callAPI(
    null,
    route,
    method,
    body,
    (data) => {
      //form_signup.reset.click();
      document.getElementById("frm-signup").reset();
      reportFail("div-signup-response", data["message"]);
      document.getElementById("btn-signup-submit").disabled = false;
    },
    (data) => {
      reportFail("div-signup-response", data);
      document.getElementById("btn-signup-submit").disabled = false;
    }
  );
});

function reportFail(id, msg) {
  document.getElementById(id).innerHTML = msg;
}

// Clear the on-screen error messages when user clicks reset
form_login.reset.addEventListener("click", (e) => {
  document.getElementById("div-login-response").innerHTML = "";
});

form_signup.reset.addEventListener("click", (e) => {
  document.getElementById("div-signup-response").innerHTML = "";
});
