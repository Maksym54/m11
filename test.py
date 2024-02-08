import unittest
from fastapi.testclient import TestClient
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_contact(self):
        contact_data = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone_number": "",
            "birthday": "",
            "additional_data": ""
        }
        response = self.client.post("/contacts/", json=contact_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["first_name"], contact_data["first_name"])

    def test_read_contacts(self):
        response = self.client.get("/contacts/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_read_contact(self):
        response = self.client.get("/contacts/1")
        self.assertEqual(response.status_code, 404)

    def test_update_contact(self):
        contact_data = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone_number": "",
            "birthday": "",
            "additional_data": ""
        }
        response = self.client.put("/contacts/1", json=contact_data)
        self.assertEqual(response.status_code, 404)

    def test_delete_contact(self):
        response = self.client.delete("/contacts/1")
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()