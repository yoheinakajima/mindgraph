# this is an example integration that automatically triggers based on an entity creation using the blinker signals by importing entity_created from app.signals.

from flask import request, current_app, jsonify
from app.signals import entity_created

def tag_person(sender, **extra):
    # Logic for tagging person goes here
    print('Tagged person with id:', extra.get('entity_id'))

def auto_tag_person(next):
    def wrapper(*args, **kwargs):
        # Call the original function and get the response directly
        response = next(*args, **kwargs)
    
        # Ensure that you only proceed if the response is a Response object and has a JSON content type
        if isinstance(response, tuple) and response[1] == 200:  # or check for other status codes if necessary
            data, status_code = response
            if status_code in (200, 201):  # Only proceed for successful responses
                # Now you can work with `data` as it is the dictionary that was meant to be JSON
                entity_type = request.view_args.get('entity_type')
    
                if request.endpoint == 'main.create_entity' and entity_type == 'people':
                    entity_id = data.get('id')
                    if entity_id:
                        # Emit the signal here, after the person has been created
                        entity_created.send(current_app._get_current_object(), entity_type='people', entity_id=entity_id)
                        print('Tagged person after creation.')
    
        # Return the original response
        return response
    return wrapper


def register(integration_manager):
    app = integration_manager.app  # Get the app instance from the manager
    entity_created.connect(tag_person, sender=app)
    
    # Apply the middleware to the create_entity view function
    integration_manager.app.view_functions['main.create_entity'] = auto_tag_person(
        integration_manager.app.view_functions['main.create_entity']
    )
    