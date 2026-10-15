import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("sara2_local", Path(__file__).resolve().parents[1] / "sara2_local.py")
sara = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sara)


class SaraLocalTests(unittest.TestCase):
    def test_unknown_command_falls_through(self):
        self.assertIsNone(sara.fast_command("поговори со мной"))

    def test_open_calculator_routes_to_process(self):
        with patch.object(sara.subprocess, "Popen") as popen:
            result = sara.fast_command("открой калькулятор")
        self.assertEqual(result, "Открываю: калькулятор")
        popen.assert_called_once()

    def test_history_round_trip_and_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory" / "history.json"
            with patch.object(sara, "MEMORY", path):
                data = [{"role": "user", "content": str(i)} for i in range(15)]
                sara.save_history(data)
                loaded = sara.load_history()
                self.assertEqual(len(loaded), 12)
                self.assertEqual(loaded[0]["content"], "3")
                self.assertEqual(loaded[-1]["content"], "14")

    def test_corrupt_history_returns_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text("{broken", encoding="utf-8")
            with patch.object(sara, "MEMORY", path):
                self.assertEqual(sara.load_history(), [])

    def test_history_write_is_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            with patch.object(sara, "MEMORY", path):
                sara.save_history([{"role": "user", "content": "Привет"}])
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))[0]["content"], "Привет")


if __name__ == "__main__":
    unittest.main()
