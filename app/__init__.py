# This code snippet demonstrates the creation of a Flask application and the initialization of custom integrations within it.

# A Flask application instance is created with specified directories for templates and static files.
# The use of relative paths ('./templates' and '../static') suggests a certain directory structure,
# indicating that templates are located in a directory within the application package and static files are outside of it.

# The application then imports and registers a Blueprint named 'main' from a local module 'views'.
# Blueprints in Flask are used to organize a group of related views and other code.
# The 'main' Blueprint likely contains route definitions for the application.

# After registering the Blueprint, the application initializes custom integrations by calling the `initialize_integrations`
# function, passing the application instance as an argument. This step dynamically loads and activates specified integrations,
# enhancing the application's functionality based on predefined configurations.

# Optionally, a list of setup callbacks can be provided to perform additional setup tasks with the application context.
# This allows for flexible customization of the application setup process, enabling the execution of additional configuration
# or initialization code after the application has been created but before it starts serving requests.

# The function returns the configured Flask application instance, ready to be used or further configured.

from flask import Flask
from .integration_manager import initialize_integrations
from .integrations.database import CurrentDBIntegration
from .models import set_database_integration
from dotenv import load_dotenv
import os

load_dotenv()


def create_app(setup_callbacks=None):
  app = Flask(__name__,
              template_folder="./templates",
              static_folder="../static")

  from .views import main

  app.register_blueprint(main)

  # Initialize integrations
  initialize_integrations(app)

  db_integration_instance = CurrentDBIntegration()
  set_database_integration(db_integration_instance)

  # If setup_callbacks is None, initialize as empty list
  setup_callbacks = setup_callbacks or []

  with app.app_context():
    for setup_callback in setup_callbacks:
      setup_callback(app)

  return app
