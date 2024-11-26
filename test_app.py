import unittest
import requests
import os

class TestFlaskApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # local URL
        cls.base_url = "http://localhost:5000"

    def test_home_page(self):
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()