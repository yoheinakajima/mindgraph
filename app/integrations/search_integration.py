# basic search

from flask import jsonify
from app.models import search_entities_with_type

def search_integration(app, data):
  with app.app_context():
      print("SEARCHING!")
      entity_type = data.get('entity_type')
      search_params = data.get('search_params')

      if entity_type and search_params:
          results = search_entities_with_type(entity_type, search_params)
          print(f"Search results: {results}")
          # Return a Flask response object
          return jsonify(results), 200
      else:
          print("Invalid search parameters")
          # Return a Flask response object
          return jsonify({"error": "Invalid search parameters"}), 400


def register(integration_manager):
    # Register this new function with the Integration Manager
    integration_manager.register('search_integration', search_integration)
