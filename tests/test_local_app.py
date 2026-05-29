import unittest
from base64 import b64encode

from src.qspice_tools.local_app import (
    _active_channel_config,
    _basic_auth_header_matches,
    _channels_from_payload,
    _default_channels,
)


class LocalAppTest(unittest.TestCase):
    def test_matches_basic_auth_header(self):
        header = "Basic " + b64encode(b"qgen:secret").decode("ascii")

        self.assertTrue(_basic_auth_header_matches(header, "qgen", "secret"))
        self.assertFalse(_basic_auth_header_matches(header, "qgen", "wrong"))
        self.assertFalse(_basic_auth_header_matches("Bearer token", "qgen", "secret"))

    def test_builds_default_four_channel_generator(self):
        channels = _default_channels()

        self.assertEqual(len(channels), 4)
        self.assertEqual(
            [channel["config"].waveform for channel in channels],
            ["Sinusoidal", "Square", "Triangle", "Arbitrary"],
        )
        self.assertEqual([channel["config"].duty_percent for channel in channels], [50.0] * 4)
        self.assertEqual([channel["config"].triangle_symmetry_percent for channel in channels], [50.0] * 4)
        self.assertEqual([channel["config"].phase_deg for channel in channels], [0.0, 90.0, 180.0, 270.0])
        self.assertEqual([channel["config"].output_load_ohms for channel in channels], [50.0] * 4)

    def test_uses_first_enabled_channel_for_qspice_input(self):
        channels = _channels_from_payload(
            {
                "channels": [
                    {
                        "enabled": False,
                        "waveform": "Sinusoidal",
                        "amplitudeV": 12,
                        "biasV": 0,
                        "frequencyHz": 10_000,
                    },
                    {
                        "enabled": True,
                        "waveform": "Triangle",
                        "amplitudeV": 5,
                        "biasV": 1,
                        "frequencyHz": 2_000,
                        "dutyPercent": 35,
                        "triangleSymmetryPercent": 60,
                        "arbitraryPoints": "0,1,0,-1,0",
                        "phaseDeg": 45,
                        "outputLoadOhms": 75,
                    },
                ]
            }
        )

        index, config = _active_channel_config(channels)

        self.assertEqual(index, 1)
        self.assertEqual(config.waveform, "Triangle")
        self.assertEqual(config.amplitude_v, 5)
        self.assertEqual(config.bias_v, 1)
        self.assertEqual(config.frequency_hz, 2_000)
        self.assertEqual(config.duty_percent, 35)
        self.assertEqual(config.triangle_symmetry_percent, 60)
        self.assertEqual(config.arbitrary_points, (0.0, 1.0, 0.0, -1.0, 0.0))
        self.assertEqual(config.phase_deg, 45)
        self.assertEqual(config.output_load_ohms, 75)

    def test_uses_selected_active_channel_for_qspice_input(self):
        channels = _channels_from_payload(
            {
                "channels": [
                    {
                        "enabled": True,
                        "waveform": "Sinusoidal",
                        "amplitudeV": 12,
                        "biasV": 0,
                        "frequencyHz": 10_000,
                    },
                    {
                        "enabled": True,
                        "waveform": "Arbitrary",
                        "amplitudeV": 4,
                        "biasV": 0,
                        "frequencyHz": 1_000,
                        "arbitraryPoints": "0,1,0",
                    },
                ]
            }
        )

        index, config = _active_channel_config(channels, active_channel=2)

        self.assertEqual(index, 1)
        self.assertEqual(config.waveform, "Arbitrary")

    def test_rejects_all_disabled_channels(self):
        channels = _channels_from_payload(
            {
                "channels": [
                    {
                        "enabled": False,
                        "waveform": "Square",
                        "amplitudeV": 12,
                        "biasV": 0,
                        "frequencyHz": 10_000,
                    }
                ]
            }
        )

        with self.assertRaisesRegex(ValueError, "At least one channel"):
            _active_channel_config(channels)


if __name__ == "__main__":
    unittest.main()
