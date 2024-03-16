# This code snippet is part of a Flask application, specifically designed for managing integrations within the app.
# It provides a structure to dynamically load and register integration functions based on the application's needs.

# The `INTEGRATIONS` dictionary specifies the available integrations and their active status. 
# True indicates an active integration that should be loaded and available for use.

# The `INTEGRATION_FUNCTIONS` dictionary is intended to store callable functions associated with each integration. 
# However, it appears to be initialized but not used directly within this snippet.

# The `IntegrationManager` class is designed to manage these integration functions. 
# It is initialized with a Flask app instance and provides a method `register` to associate integration names 
# with their corresponding callable functions, effectively making them available application-wide.

# The `get_integration_function` function retrieves a callable integration function by its name from the Flask app's 
# `integration_manager`, allowing for easy access to integration functionalities throughout the app.

# The `initialize_integrations` function is responsible for initializing the `IntegrationManager` with the Flask app 
# and dynamically loading integration modules from a specified directory. It checks the `INTEGRATIONS` dictionary to 
# determine if an integration is active, and if so, it imports the module, checks for a `register` function, and 
# executes it to register the integration. This dynamic loading mechanism allows for flexible integration management, 
# enabling or disabling integrations as needed without modifying the core application code.



# app/integration_manager.py
import os
import importlib
from flask import Flask, current_app

# Dictionary to hold the status of integrations
INTEGRATIONS = {
    'auto_add_person': False,
    'auto_tag_person': False,
    'search_integration': True,
    'conditional_person_addition': True,
    'conditional_entity_addition': True,
    'conditional_relationship_addition': True,
    'add_multiple_conditional': True,
    'natural_input': True,
    'natural_input_flexible': True,
    'url_input': True,
    'url_array_processor' : True,
    'latent_input' : True,
    'ai_search' : True
}

# This dictionary will hold callable integration functions
INTEGRATION_FUNCTIONS = {}

class IntegrationManager:
    def __init__(self, app):
        self.app = app
        self.integration_functions = {}

    def register(self, integration_name, integration_function):
        # Register the callable function for the integration
        self.integration_functions[integration_name] = integration_function
        #self.app.before_request_funcs.setdefault(None, []).append(integration_function)

def get_integration_function(integration_name):
  # Retrieve a callable integration function by name
  return current_app.integration_manager.integration_functions.get(integration_name)

def initialize_integrations(app):
  app.integration_manager = IntegrationManager(app)

  integrations_dir = os.path.join(app.root_path, 'integrations')
  for module_name in os.listdir(integrations_dir):
      if module_name == '__init__.py' or module_name == '__pycache__' or not module_name.endswith('.py'):
          continue
      integration_name = module_name[:-3]
      if INTEGRATIONS.get(integration_name):
          module_path = f'app.integrations.{integration_name}'
          mod = importlib.import_module(module_path)
          if hasattr(mod, 'register'):
              mod.register(app.integration_manager)
