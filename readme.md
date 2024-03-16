# MindGraph

Welcome to MindGraph, a proof of concept, open-source, API-first graph-based project designed for natural language interactions (input and output). This prototype serves as a template for building and customizing your own CRM solutions with a focus on ease of integration and extendibility.

## Getting Started

### Prerequisites
Before you begin, ensure you have the following installed:
- Python 3.6 or higher
- Flask, which can be installed via pip:

```sh
pip install Flask
```

## Running the Application

After cloning the repository, navigate to the root directory and start the Flask server with:

```sh
python main.py
```

The server will launch on `http://0.0.0.0:81`.

## Project Structure

MindGraph is organized into several key components:

- `main.py`: The entry point to the application.
- `app/__init__.py`: Sets up the Flask app and integrates the blueprints.
- `models.py`: Manages the in-memory graph data structure for entities and relationships.
- `views.py`: Hosts the API route definitions.
- `integration_manager.py`: Handles the dynamic registration and management of integration functions.
- `signals.py`: Sets up signals for creating, updating, and deleting entities.

## Integration System

MindGraph employs a sophisticated integration system designed to extend the application's base functionality dynamically. At the core of this system is `integration_manager.py`, which acts as a registry and executor for various integration functions. This modular architecture allows AutoPlex to incorporate AI-powered features seamlessly, such as processing natural language inputs into structured knowledge graphs through integrations like `natural_input.py`. Further integrations, including `add_multiple_conditional`, `conditional_entity_addition`, and `conditional_relationship_addition`, work in tandem to ensure the integrity and enhancement of the application's data model.

## Features

**Entity Management**: Entities are stored in an in-memory graph for quick access and manipulation, allowing CRUD operations on people, organizations, and their interrelations.

**Integration Triggers**: Custom integration functions can be triggered via HTTP requests, enabling the CRM to interact with external systems or run additional processing.

**Search Capabilities**: Entities and their relationships can be easily searched with custom query parameters.

**AI Readiness**: Designed with AI integrations in mind, facilitating the incorporation of intelligent data processing and decision-making.

## API Endpoints

MindGraph provides a series of RESTful endpoints:

- `POST /<entity_type>`: Create an entity.
- `GET /<entity_type>/<int:entity_id>`: Retrieve an entity.
- `GET /<entity_type>`: List all entities of a type.
- `PUT /<entity_type>/<int:entity_id>`: Update an entity.
- `DELETE /<entity_type>/<int:entity_id>`: Remove an entity.
- `POST /relationship`: Establish a new relationship.
- `GET /search/entities/<entity_type>`: Search for entities.
- `GET /search/relationships`: Find relationships.

### Custom Integration Endpoint

- `POST /trigger-integration/<integration_name>`: Activates a predefined integration function.

## Development & Extension

### Adding New Integrations

To incorporate a new integration into AutoPlex, create a Python module within the `integrations` directory. This module should define the integration's logic and include a `register` function that connects the integration to the `IntegrationManager`. Ensure that your integration interacts properly with the application's components, such as `models.py` for data operations and `views.py` for activation via API endpoints. This approach allows AutoPlex to dynamically expand its capabilities through modular and reusable code.

### Utilizing Signals

Signals are emitted for entity lifecycle events, providing hooks for extending functionality or syncing with other systems.

## Example Command

To create a person via `curl`:

```sh
curl -X POST http://0.0.0.0:81/people \
-H "Content-Type: application/json" \
-d '{"name":"Jane Doe","age":28}'
```

### Example Use Cases

To demonstrate the power of MindGraph's integration system, here are some example commands:

#### Triggering Natural Input Integration

```sh
curl -X POST http://0.0.0.0:81/trigger-integration/natural_input \
-H "Content-Type: application/json" \
-d '{"input":"Company XYZ organized an event attended by John Doe and Jane Smith."}'
```

## Contributions

Let's be honest... I don't maintain projects. If you want to take over/manage this, let me know (X/Twitter is a good channel). Otherwise, enjoy this proof of concept starter kit as it is :)

## License

MindGraph is distributed under the MIT License. See `LICENSE` for more information.

## Contact

Just tag me on Twitter/X [https://twitter.com/yoheinakajima](@yoheinakajima)

Project Link: [https://github.com/yoheinakajima/MindGraph](https://github.com/yoheinakajima/MindGraph)
