# This code snippet defines a simple in-memory graph data structure to simulate a database for storing and managing entities
# such as people, organizations, events, and their relationships. It uses a Python dictionary to hold the graph data and
# a global variable for unique entity IDs. Functions provided include:
# - add_entity: Adds a new entity (e.g., person, organization, event) to the graph with a unique ID, incrementing the ID counter.
# - get_full_graph: Returns the entire graph data including all entities and relationships.
# - get_entity: Retrieves a specific entity by its type and ID.
# - get_all_entities: Returns all entities of a specific type.
# - update_entity: Updates an entity's data if it exists in the graph.
# - delete_entity: Removes an entity from the graph by its type and ID.
# - add_relationship: Adds a relationship between entities to the graph.
# - search_entities: Searches for entities based on a set of search parameters.
# - search_entities_with_type: Searches for entities of a specific type based on search parameters.
# - search_relationships: Searches for relationships that match given search parameters.
# This representation is basic and intended for demonstration or prototyping. For production use, a database and an ORM (Object-Relational Mapping) should be utilized for data persistence and management.

# This is a very basic representation. For a real application, use a database and ORM.
from .base import DatabaseIntegration

next_id = 1


class InMemoryDatabase(DatabaseIntegration):

  def __init__(self):
    self.graph = {
        "entities": {},  # Stores all entities by type and then by ID
        "relationships": [],  # Stores relationships
    }

  def add_entity(self, entity_type, data):
    print("add_entity")
    print(self.add_entity)
    global next_id
    entity_id = next_id
    if entity_type not in self.graph["entities"]:
      self.graph["entities"][entity_type] = {}
    self.graph["entities"][entity_type][entity_id] = data
    next_id += 1
    print(f"Added {entity_type} with ID: {entity_id}, next ID: {next_id}")
    return entity_id

  def get_full_graph(self):
    return self.graph

  def get_entity(self, entity_type, entity_id):
    return self.graph["entities"].get(entity_type, {}).get(entity_id)

  def get_all_entities(self, entity_type):
    return self.graph["entities"].get(entity_type, {})

  def update_entity(self, entity_type, entity_id, data):
    entities = self.graph["entities"].get(entity_type)
    if entities and entity_id in entities:
      entities[entity_id].update(data)
      return True
    return False

  def delete_entity(self, entity_type, entity_id):
    entities = self.graph["entities"].get(entity_type)
    if entities and entity_id in entities:
      # Delete the entity from the entities dictionary
      del entities[entity_id]

      # Filter out relationships involving the deleted entity
      self.graph["relationships"] = [
          relationship for relationship in self.graph["relationships"]
          if relationship["from_id"] != entity_id
          and relationship["to_id"] != entity_id
      ]

      return True
    return False

  def add_relationship(self, data):
    self.graph["relationships"].append(data)
    return len(self.graph["relationships"])

  def search_entities(self, search_params):
    results = []
    for entity_type, entities in self.graph["entities"].items():
      for entity_id, entity_details in entities.items():
        entity_info = entity_details.get("data", {})
        # Convert values to strings for comparison
        if all(
            str(value).lower() in str(entity_info.get(key, "")).lower()
            for key, value in search_params.items()):
          results.append({"type": entity_type, "id": entity_id, **entity_info})
    return results

  def search_entities_with_type(self, entity_type, search_params):
    results = []
    for entity_id, entity_details in self.graph["entities"].get(entity_type, {}).items():
      entity_info = entity_details.get("data", {})
      # Convert values to strings for comparison
      if all(
          str(value).lower() in str(entity_info.get(key, "")).lower()
          for key, value in search_params.items()):
        results.append({"type": entity_type, "id": entity_id, **entity_info})
    return results

  def search_relationships(self, search_params):
    results = []
    for relationship in self.graph["relationships"]:
      # Convert values to strings for comparison
      if all(
          str(value).lower() in str(relationship.get(key, "")).lower()
          for key, value in search_params.items()):
        results.append(relationship)
    return results
