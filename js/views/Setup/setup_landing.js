import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  reloadMessage,
  decode_jwt,
  populate_aside,
} from "../../common_funcs.js";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <p class="welcome-message">
      Welcome to the setup side of the <strong>Duck Club App</strong>
    </p>
    <h1 class="heading-primary">How it Works</h1>
    <section class="instructions">
      <article class="instruction">
        <div class="step-text-box">
          <p class="step-num">01</p>
          <h3 class="heading-tertiary">Pre-Hunt Setup</h3>
          <p class="step-description">
            Using the navigation menu on the left, members and managers setup the hunt.
            This includes hunter sign up, group formation, and pond assignments.
          </p>
        </div>
      </article>
      <img src="img/left-arrow.png" class="step-img">
      <img src="img/Masters-leaderboard.jpg" class="step-img">
      <article class="instruction">
        <div class="step-text-box">
          <p class="step-num">02</p>
          <h3 class="heading-tertiary">During the Hunt</h3>
          <p class="step-description">
            All members can watch the live leaderboard to see which groups are
            having the best hunt (as well as bird species). Members participating
            in the hunt can update their harvest results so that other groups know
            where they stand.
          </p>
        </div>
      </article>
      <article class="instruction">
        <div class="step-text-box">
          <p class="step-num">03</p>
          <h3 class="heading-tertiary">Statistics</h3>
          <p class="step-description">
            Using data entered by fellow members as they hunt, members can access
            a variety of different stats. Results can be for the whole club or
            filtered to just the indivitual member. Results are shown by hunter,
            date, species, and pond. You can see who's been on the most hunts
            and who's leading the club in both total and average harvest!
          </p>
        </div>
      </article>
      <img src="img/chart.png" class="step-img">
    </section>

    <h1 class="heading-primary">Notes</h1>
    <section class="cards">
      <article class="card">
        <img src="img/machine.jpg" class="card-img">
        <div class="card-content">
          <div class="card-title">Hunt Lifecycle</div>
          <ul>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Signup Open</span>
            </li>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Signup Closed</span>
            </li>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Draw Complete</span>
            </li>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Hunt Open</span>
            </li>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Hunt Closed</span>
            </li>
          </ul>
        </div>
      </article>
      <article class="card">
        <img src="img/baby_ducks.jpg" class="card-img">
        <div class="card-content">
          <div class="card-title">Future Features</div>
          <ul>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Scouting report</span>
            </li>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Guest signup</span>
            </li>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Members form their own groups</span>
            </li>
            <li>
              <img src="img/Birds-Silhouettes-Duck2.svg" class="card-icon">
              <span>Leaderboard automatically updates</span>
            </li>
          </ul>
        </div>
      </article>
    </section>
    `;
  }

  js(jwt) {
    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside(user_level);
  }
}
