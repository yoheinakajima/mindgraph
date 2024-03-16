# This Flask application integration, `add_multiple_conditional`, dynamically adds multiple entities and relationships
# to a knowledge graph, leveraging other integrations `conditional_entity_addition` and `conditional_relationship_addition`.

# It starts by attempting to load these integrations using `get_integration_function`, to conditionally add entities
# and their relationships. The data processed includes entities (`nodes`) and relationships, with entities addressed first.

# Entities are added through `conditional_entity_add_function`, with a payload prepared for each entity containing its type
# and data. The response updates a mapping of temporary IDs to actual system-assigned IDs, essential for linking entities
# in relationships accurately.

# Post entities addition, it iterates over the `relationships` data, using the entity ID mapping to construct a payload
# for each relationship. This payload is then passed to `conditional_relationship_add_function`, which decides on the
# relationship's addition based on internal logic.

# The function prints outcomes (e.g., entity added, relationship exists) and handles errors gracefully, returning a JSON
# response with the operation's status and details on created or matched entities and relationships.

# A `register` function ensures `add_multiple_conditional` is available within the application's integration manager,
# enabling its invocation as part of the application's integrations ecosystem.

# This approach demonstrates complex data processing and dynamic integration invocation within a Flask application for
# enhanced knowledge graph management.

# app/integrations/add_multiple_nodes_and_relationships.py
from flask import jsonify
from app.integration_manager import get_integration_function


def add_multiple_conditional(app, data):
  with app.app_context():
    try:
      print(f"\n\nData received: {data}\n\n")
      print("ADD MULTIPLE NODES AND RELATIONSHIP INTEGRATION STARTED")
      created_entities = {}
      entity_names = {}

      # Retrieve the callable functions for the conditional additions
      conditional_entity_add_function = get_integration_function(
          "conditional_entity_addition")
      conditional_relationship_add_function = get_integration_function(
          "conditional_relationship_addition")

      if (not conditional_entity_add_function
          or not conditional_relationship_add_function):
        raise ValueError("Integration function(s) not found")

      # Handle entity additions
      for entity_type, entities in data["nodes"].items():
        created_entities[entity_type] = {}

        for entity in entities:
          temp_id = entity["temp_id"]
          name = entity["name"]
          entity_names[temp_id] = name
          print(f"\nEntity {temp_id} with name {name} added\n")

        for entity_data in entities:
          # Prepare the payload as expected by the conditional_entity_addition
          payload = {"entity_type": entity_type, "data": entity_data}
          # Use conditional_entity_addition to add the entity
          response, status_code = conditional_entity_add_function(app, payload)

          if status_code != 200:
            # Handle non-OK responses accordingly
            print(f"Error while adding entity: {response}")
            continue

          response_data = response.get_json()
          print(response_data)

          if not response_data["success"]:
            # Handle the case where the entity already exists
            print(
                f"Match found, using existing {entity_type} with data: {response_data.get('match_data')}"
            )
          else:
            # Handle the case where a new entity is created
            print(
                f"New {entity_type} added with data: {response_data.get('created_data')}"
            )

          # Map temp_id to the actual entity identifier
          created_entities[entity_type][entity_data.get("temp_id")] = (
              response_data.get("entity_id", response_data.get("match_id")))

          print(f"\n\nEntity Names: {entity_names}\n\n")

      # Handle relationship additions
      for relationship in data["relationships"]:
        from_temp_id = relationship["from_temp_id"]
        to_temp_id = relationship["to_temp_id"]
        relationship_data = relationship["data"]

        from_id = created_entities[relationship["from_type"]][
            relationship["from_temp_id"]]
        to_id = created_entities[relationship["to_type"]][
            relationship["to_temp_id"]]
        relationship_data = relationship["data"]
        relationship_data["from_id"] = from_id
        relationship_data["to_id"] = to_id
        relationship_data["from_type"] = relationship["from_type"]
        relationship_data["to_type"] = relationship["to_type"]
        relationship_data["from_entity"] = entity_names[from_temp_id]
        relationship_data["to_entity"] = entity_names[to_temp_id]
        relationship_data["relationship_type"] = relationship.get(
            "relationship",
            "associated")  # Default to 'associated' if no type provided

        # Use conditional_relationship_addition to add the relationship
        response, status_code = conditional_relationship_add_function(
            app, relationship_data)

        if status_code != 200:
          # Handle non-OK responses accordingly
          print(f"Error while adding relationship: {response}")
          continue

        response_data = response.get_json()

        if not response_data["success"]:
          # Handle the case where the relationship already exists
          print(
              f"Match found, relationship already exists with data: {response_data.get('match_data')}"
          )
        else:
          # Handle the case where a new relationship is created
          print(f"New relationship added with data: {relationship_data}")

      return jsonify({
          "success": True,
          "created_entities": created_entities
      }), 200
    except Exception as e:
      print(f"Failed to add multiple nodes and relationships: {e}")
      return jsonify({"error": str(e)}), 500


def register(integration_manager):
  integration_manager.register("add_multiple_conditional",
                               add_multiple_conditional)
