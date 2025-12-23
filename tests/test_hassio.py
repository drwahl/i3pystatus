"""
Basic test for the hassio module
"""

import subprocess
import unittest
from mock import patch, MagicMock
from requests import get
from i3pystatus import hassio
import json

# inline json of hassio api response
STREAM = {'attributes': {'friendly_name': 'Light',
                         'node_id': 18,
                         'supported_features': 1,
                         'value_id': '72054591347734729',
                         'value_index': 0,
                         'value_instance': 1},
          'context': {'id': '54188133d21271036bbfb089019a3481',
                      'parent_id': None,
                      'user_id': None},
          'entity_id': 'light.living_room',
          'last_changed': '2021-02-24T23:37:25.627676+00:00',
          'last_updated': '2021-02-24T23:37:25.627676+00:00',
          'state': 'off'}

HASSIO_URL = 'http://localhost:8123'
FAKETOKEN = 'ihasatoken'


class HassioTest(unittest.TestCase):

    @patch('i3pystatus.hassio.get', autospec=True)
    def test_not_desired_state(self, get):
        """
        Test output when state matches desired state
        """
        hassio.get.return_value.text = json.dumps(STREAM)
        hassiostat = hassio.Hassio(entity_id='light.living_room',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN,
                                   good_color="#00FF00",
                                   bad_color="#FF0000",
                                   desired_state='on')
        hassiostat.run()
        self.assertTrue(hassiostat.output == {'full_text': 'Light: off', 'color': '#FF0000'})

    @patch('i3pystatus.hassio.get', autospec=True)
    def test_desired_state(self, urlopen):
        """
        Test output from side-loaded xml (generated from a real hassio server
        response)
        """
        hassio.get.return_value.text = json.dumps(STREAM)
        hassiostat = hassio.Hassio(entity_id='light.living_room',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN,
                                   good_color="#00FF00",
                                   bad_color="#FF0000",
                                   desired_state='off')
        hassiostat.run()
        self.assertTrue(hassiostat.output == {'full_text': 'Light: off', 'color': '#00FF00'})

    @patch('i3pystatus.hassio.post', autospec=True)
    def test_toggle(self, mock_post):
        """
        Test that toggle calls the correct Home Assistant API endpoint
        """
        hassiostat = hassio.Hassio(entity_id='light.living_room',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN)
        hassiostat.toggle()

        # Verify post was called with correct URL and payload
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        expected_url = '%s/api/services/light/toggle' % HASSIO_URL
        self.assertEqual(call_args[0][0], expected_url)
        self.assertEqual(call_args[1]['json'], {'entity_id': 'light.living_room'})
        # Verify authorization header
        self.assertIn('Authorization', call_args[1]['headers'])
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer %s' % FAKETOKEN)

    @patch('i3pystatus.hassio.post', autospec=True)
    def test_toggle_switch_domain(self, mock_post):
        """
        Test that toggle extracts the correct domain from entity_id
        """
        hassiostat = hassio.Hassio(entity_id='switch.garage_door',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN)
        hassiostat.toggle()

        # Verify post was called with switch domain
        call_args = mock_post.call_args
        expected_url = '%s/api/services/switch/toggle' % HASSIO_URL
        self.assertEqual(call_args[0][0], expected_url)
        self.assertEqual(call_args[1]['json'], {'entity_id': 'switch.garage_door'})

    @patch('i3pystatus.hassio.get', autospec=True)
    def test_refresh(self, mock_get):
        """
        Test that refresh calls run() to update state
        """
        hassio.get.return_value.text = json.dumps(STREAM)
        hassiostat = hassio.Hassio(entity_id='light.living_room',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN)
        hassiostat.refresh()

        # Verify get was called (run() fetches state)
        mock_get.assert_called_once()
        # Verify output was updated
        self.assertIsNotNone(hassiostat.output)

    @patch('i3pystatus.hassio.subprocess.Popen')
    def test_open_dashboard(self, mock_popen):
        """
        Test that open_dashboard opens browser with correct URL
        """
        hassiostat = hassio.Hassio(entity_id='light.living_room',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN)
        hassiostat.open_dashboard()

        # Verify Popen was called with default browser command and output suppressed
        mock_popen.assert_called_once_with(
            ['xdg-open', HASSIO_URL],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @patch('i3pystatus.hassio.subprocess.Popen')
    def test_open_dashboard_custom_browser(self, mock_popen):
        """
        Test that open_dashboard uses custom browser_cmd setting
        """
        hassiostat = hassio.Hassio(entity_id='light.living_room',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN,
                                   browser_cmd='firefox')
        hassiostat.open_dashboard()

        # Verify Popen was called with custom browser command and output suppressed
        mock_popen.assert_called_once_with(
            ['firefox', HASSIO_URL],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def test_default_click_handlers(self):
        """
        Test that default click handlers are set correctly
        """
        hassiostat = hassio.Hassio(entity_id='light.living_room',
                                   hassio_url=HASSIO_URL,
                                   hassio_token=FAKETOKEN)
        self.assertEqual(hassiostat.on_leftclick, 'toggle')
        self.assertEqual(hassiostat.on_middleclick, 'refresh')
        self.assertEqual(hassiostat.on_rightclick, 'open_dashboard')


if __name__ == '__main__':
    unittest.main()
