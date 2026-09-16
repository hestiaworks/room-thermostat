/**
 * Room Thermostat — the page.
 *
 * A shell at this point: it proves the route, the registration and the module
 * load. Rooms, the house and the history arrive in the next plan.
 */
class RoomThermostatPage extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  connectedCallback() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.render();
  }

  render() {
    if (!this.shadowRoot) return;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; padding: 24px; font-family: system-ui, sans-serif; }
      </style>
      <h1>Room Thermostat</h1>
      <p>The page is registered and loading.</p>
    `;
  }
}

/*
 * Home Assistant instantiates `ha-panel-<component_name>` for a panel
 * registered from an integration, so that is the name that has to exist. The
 * bare name is defined too, for anyone embedding the element directly.
 */
if (!customElements.get("ha-panel-room-thermostat-page")) {
  customElements.define("ha-panel-room-thermostat-page", RoomThermostatPage);
}
if (!customElements.get("room-thermostat-page")) {
  customElements.define(
    "room-thermostat-page",
    class extends RoomThermostatPage {},
  );
}
