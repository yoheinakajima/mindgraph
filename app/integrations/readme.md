# Building Integraions into AutoPlex

Integrations are external or additional features that extend the base functionality of AutoPlex. They are managed within `IntegrationManager`, which acts as a registry and executor for these features.

## The Integration Manager

The `IntegrationManager` is a crucial component in managing integrations:

- It serves as a central registry, holding a dictionary of callable integration functions.
- It enables modular and decoupled design, allowing the application to invoke integrations by name.
- During the app's initialization, the `initialize_integrations` function sets up the `IntegrationManager` and loads all enabled integrations from the `integrations` directory, using the `INTEGRATIONS` dictionary to check which ones are enabled.

## Model Functions

Model functions are the operations that handle the manipulation of data within the application. In a production environment, these would typically interface with a database using an ORM. The functions include:

- `add_entity`: Add a new entity to the application's data store.
- `get_entity`: Retrieve an entity's data.
- `update_entity`: Update an existing entity's data.
- `delete_entity`: Remove an entity from the data store.
- `add_relationship`: Create a relationship between entities.
- `search_entities`: Search for entities that meet certain criteria.
- `search_relationships`: Find relationships based on specific parameters.

## API Endpoints

API endpoints allow external sources to interact with the Flask application. They are defined with Flask's routing decorators and handle incoming HTTP requests:

```python
@main.route('/trigger-integration/<integration_name>', methods=['POST'])
def trigger_integration(integration_name):
    # This endpoint triggers an integration using the provided name in the POST request.
```

## Trigger-Based Integrations

Integrations can also be designed to respond to internal events within the application using Flask's signal system:

- Signals like `entity_created` are emitted to indicate specific actions or changes, such as the creation of a new entity.
- Functions connected to these signals act as listeners and perform tasks in response to the events.

## Connecting Functions to Signals

To establish a connection between a function and a signal, use the `connect` method:

```python
entity_created.connect(tag_person, sender=app)
```

With this connection, the `tag_person` function will be executed whenever the `entity_created` signal is emitted by the application.

## Invoking Other Integrations

Integrations can be designed to trigger other integrations. This is done by retrieving the callable function of another integration and executing it with the necessary data:

```python
add_person_integration_function = get_integration_function('event_triggered_person_addition')
```

## Steps to Create a New Integration

Here's how you can create and incorporate a new integration into a Flask application:

### 1. Create the Integration Logic
Define the main logic of the integration as a Python module in the `integrations` directory.

### 2. Register the Integration
In the module, create a `register` function to register the integration with the `IntegrationManager`.

### 3. Enable the Integration
Add the integration name to the `INTEGRATIONS` dictionary in `integration_manager.py` and set its value to `True`.

### Optional Components

Depending on the integration's needs, you may also:

- **Use Model Functions (Optional)**: Interact with the application's data model by importing and using model functions.
- **Set Up an API Endpoint**: For integrations invoked via HTTP requests, define a corresponding endpoint in `views.py`.
- **Connect to Signals (Optional)**: For event-driven integrations, connect your functions to Flask signals within the `register` function.
- **Invoke Other Integrations (Optional)**: For complex workflows, use other integrations by retrieving them with `get_integration_function`.

Each integration can vary in complexity and purpose, requiring different combinations of these steps to be fully implemented.
