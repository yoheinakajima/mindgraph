import unittest
from app import create_app
from app.models import graph, add_entity, get_entity, update_entity, delete_entity, add_relationship

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        # Create the Flask application for testing
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Initialize the in-memory data store
        graph['people'] = {}
        graph['organizations'] = {}
        graph['events'] = {}
        graph['relationships'] = []

        # Create initial test data
        self.person_id = add_entity('people', {
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        self.organization_id = add_entity('organizations', {
            'name': 'Doe Enterprises'
        })
        self.event_id = add_entity('events', {
            'name': 'Annual Meeting',
            'location': 'Conference Center'
        })
        self.relationship_id = add_relationship({
            'type': 'employment',
            'person_id': self.person_id,
            'organization_id': self.organization_id
        })

    def tearDown(self):
        # Clear the in-memory data store
        self.app_context.pop()

    def test_create_person(self):
        response = self.client.post('/people', json={
            'name': 'Jane Doe',
            'email': 'jane@example.com'
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)

    def test_get_person(self):
        response = self.client.get(f'/people/{self.person_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('name', data)

    def test_update_person(self):
        response = self.client.put(f'/people/{self.person_id}', json={
            'name': 'John Doe Updated'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_delete_person(self):
        response = self.client.delete(f'/people/{self.person_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_create_organization(self):
        response = self.client.post('/organizations', json={
            'name': 'New Org'
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)

    def test_get_organization(self):
        response = self.client.get(f'/organizations/{self.organization_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('name', data)

    def test_update_organization(self):
        response = self.client.put(f'/organizations/{self.organization_id}', json={
            'name': 'Doe Enterprises Updated'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_delete_organization(self):
        response = self.client.delete(f'/organizations/{self.organization_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_create_event(self):
        response = self.client.post('/events', json={
            'name': 'New Event',
            'location': 'New Venue'
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)

    def test_get_event(self):
        response = self.client.get(f'/events/{self.event_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('name', data)

    def test_update_event(self):
        response = self.client.put(f'/events/{self.event_id}', json={
            'name': 'Annual Meeting Updated'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_delete_event(self):
        response = self.client.delete(f'/events/{self.event_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_create_relationship(self):
        response = self.client.post('/relationship', json={
            'type': 'partnership',
            'person_id': self.person_id,
            'organization_id': self.organization_id
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)

if __name__ == '__main__':
    unittest.main()
