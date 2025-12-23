from i3pystatus import IntervalModule
from requests import get, post
import json
import subprocess


class Hassio(IntervalModule):
    """
    Displays the state of a Homeassistant.io entity
    Requires the PyPI package `requests`

    Left click toggles the entity state (for switches, lights, etc.)
    Middle click forces a refresh of the current state.
    Right click opens the Home Assistant dashboard in a browser.
    """

    settings = (
        ("entity_id", "Entity ID to track."),
        ("hassio_url", "URL to your hassio install. (default: "
            "https://localhost:8123)"),
        ("hassio_token", "HomeAssistant API token "
            "(https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token)"),
        ("interval", "Update interval."),
        ("desired_state", "The desired or \"good\" state of the entity."),
        ("good_color", "Color of text while entity is in desired state"),
        ("bad_color", "Color of text while entity is not in desired state"),
        "format",
        ("hide_state", "State value used to determine if the results should be hidden"),
        ("browser_cmd", "Command to open browser (default: xdg-open)"),
    )
    required = ("hassio_url", "hassio_token", "entity_id")
    desired_state = "on"
    good_color = "#00FF00"     # green
    bad_color = "#FF0000"      # red
    interval = 15
    hide_state = None
    format = "{friendly_name}: {state}"
    browser_cmd = "xdg-open"

    on_leftclick = "toggle"
    on_middleclick = "refresh"
    on_rightclick = "open_dashboard"

    def run(self):
        headers = {"content-type": "application/json",
                   "Authorization": "Bearer %s" % self.hassio_token}
        url = "%s/api/states/%s" % (self.hassio_url, self.entity_id)
        response = get(url, headers=headers)
        entity = json.loads(response.text)

        cdict = {
            "friendly_name": entity['attributes']['friendly_name'] or None,
            "entity_id": entity['entity_id'] or self.entity_id,
            "last_change": entity['last_changed'] or None,
            "last_update": entity['last_updated'] or None,
            "state": entity['state']
        }

        color = self.good_color if entity['state'] == self.desired_state else self.bad_color
        if entity['state'] == self.hide_state:
            self.output = {"full_text": ''}
        else:
            self.output = {
                "full_text": self.format.format(**cdict),
                "color": color
            }

    def toggle(self):
        """Toggle the entity state (for switches, lights, input_booleans, etc.)"""
        headers = {"content-type": "application/json",
                   "Authorization": "Bearer %s" % self.hassio_token}
        # Extract domain from entity_id (e.g., "light" from "light.living_room")
        domain = self.entity_id.split('.')[0]
        url = "%s/api/services/%s/toggle" % (self.hassio_url, domain)
        post(url, headers=headers, json={"entity_id": self.entity_id})

    def refresh(self):
        """Force a refresh of the current state"""
        self.run()

    def open_dashboard(self):
        """Open the Home Assistant dashboard in a browser"""
        subprocess.Popen(
            [self.browser_cmd, self.hassio_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
