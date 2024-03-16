# This is an integration for the NexusDB database (https://www.nexusdb.io)
# NexusDB is a new, all-in-one cloud database for graphs, tables, documents, files,
# vectors, and more. It allows you to connet all these database types in one place
# and access a shared knowledge graph where anyone can upload and share information.
# More information about all of this can be found in the nexus docs
# (https://nexusdb.readthedocs.io/en/latest/), more documentation is coming
# soon but in the meantime you can reference the python API
# at https://github.com/Astra-Analytics/nexus-python

# We are currently looking for design partners and investors! If interested please reach
# out to us at info@nexusdb.io

import json
import os
from typeid import TypeID, get_prefix_and_suffix as typeid_prefix

from nexus_python.nexusdb import NexusDB

from .base import DatabaseIntegration
from .memory import InMemoryDatabase

relation_prefix = os.environ.get("NEXUSDB_SCHEMA_PREFIX")
if os.environ.get("NEXUSDB_USE_SHARED_GRAPH") == "True":
  graph_relation = "Graph"
else:
  graph_relation = f"{relation_prefix}_Graph"


class NexusDBIntegration(InMemoryDatabase, DatabaseIntegration):

  def __init__(self, schema_file_path="schema.json"):
    self.nexus_db = NexusDB()  # Placeholder for NexusDB connection setup
    self.schema = self._load_schema(schema_file_path)
    self._ensure_db_schema()
    self.graph = self._fetch_initial_graph()

  def _load_schema(self, schema_file_path):
    # Load and return the schema from the schema.json file
    with open(schema_file_path, "r") as file:
      schema = json.load(file)
    return schema

  def _ensure_db_schema(self):
    # Check existing database schema against the loaded schema
    print("Checking database schema...")
    for node_type, details in self.schema.items():
      relation_name = f"{relation_prefix}_{node_type}"
      # print(f"Checking relation: {relation_name}")
      status = self.nexus_db.lookup(relation_name, fields=None, condition="")
      # print(f"Status: {status}\n\n")

      if status == "Error retrieving data from server":
        # Convert details to fields format expected by NexusDB
        edge_types = details.get("edge_types", {})
        # Apply special character rules for each column name
        fields = [{
            "name": edge.replace("/", "_or_").replace(" ", "_")
        } for edge in edge_types]

        print(f"Creating relation: {relation_name} with columns: {fields}\n\n")
        create_relation = self.nexus_db.create(relation_name, fields)
        print(f"create_relation: {create_relation}\n\n")
      else:

        try:
          # Attempt to parse the status as JSON
          status_dict = json.loads(status)
        except json.JSONDecodeError:
          # If status is not valid JSON, handle the error or log it
          print("Error decoding JSON from status")
          continue  # Skip to the next iteration if JSON is invalid

        existing_headers = status_dict.get("headers", [])
        schema_fields = details.get("edge_types", {}).keys()
        # Convert schema fields according to the naming rules applied when creating columns
        schema_fields_converted = [
            field.replace("/", "_or_").replace(" ", "_")
            for field in schema_fields
        ]
        missing_fields = [
            field for field in schema_fields_converted
            if field not in existing_headers
        ]

        if missing_fields:
          print(
              f"Updating relation: {relation_name} with missing fields: {missing_fields}\n\n"
          )
          self._update_table_schema(relation_name, missing_fields)

  def _update_table_schema(self, relation_name, missing_fields):
    add_columns = {
        "fields": missing_fields,  # List of field names to add
        "defaults": ["null" for _ in missing_fields
                     ],  # Corresponding list of default values for each field
    }

    # Call the edit_fields method with the correctly formatted add_columns
    result = self.nexus_db.edit_fields(
        relation_name=relation_name,
        add_columns=add_columns,  # This matches the expected JSON structure
        condition="",  # Assuming you're not using a condition for this operation
    )
    print(f"Result of updating schema: {result}\n\n")
    return result

  def _fetch_initial_graph(self):
    # Placeholder method to fetch initial graph data from NexusDB
    status = self.nexus_db.lookup(graph_relation, fields=None, condition="")

    if status == "Error retrieving data from server":
      field_names = [
          "sourceId",
          "sourceName",
          "relationship",
          "targetId",
          "targetName",
      ]

      fields = [{"name": field} for field in field_names]

      create_relation = self.nexus_db.create(graph_relation, fields)
      print(f"Creating relation: {graph_relation} with fields: {fields}\n\n")

    entities_data = self.nexus_db.join(
        join_type="Outer",
        relations=[
            {
                "relation_name": graph_relation,
                "fields": ["sourceId", "sourceName"]
            },
            {
                "relation_name": graph_relation,
                "fields": ["targetId", "targetName"]
            },
        ],
        return_fields=["id", "name"],
    )

    try:
      entities_data = json.loads(entities_data)

      entities = {}

      for row in entities_data["rows"]:
        id_str = row[0]["Str"]
        name = row[1]["Str"]

        if "Err(" in name:
          continue

        # Determine the entity type from the ID using the typeid_prefix function
        raw_entity_type, _ = typeid_prefix(id_str)
        entity_type = raw_entity_type.title()

        if entity_type not in entities:
          entities[entity_type] = {}

        cleaned_name = name.replace('"', "")

        entities[entity_type][id_str] = {
            "entity_type": entity_type,
            "data": {
                "id": id_str,
                "name": cleaned_name
            },
        }
    except Exception as e:
      print(f"Error parsing entities data: {e}")
      entities = {}

    relationships_data = self.nexus_db.lookup(
        graph_relation,
        fields=["relationship", "snippet", "sourceId", "targetId"],
        condition=
        "snippet=concat(sourceName, ' ', relationship, ' -> ', targetName)",
    )

    try:
      relationships_data = json.loads(relationships_data)

      relationships = []

      for row in relationships_data["rows"]:
        relationship_type = row[0]["Str"]
        snippet = row[1]["Str"].replace('"', "")
        source_id = row[2]["Str"]
        target_id = row[3]["Str"]

        if "Err(" in snippet:
          continue

        source_entity_type, _ = typeid_prefix(source_id)
        target_entity_type, _ = typeid_prefix(target_id)

        relationship_entry = {
            "relationship": relationship_type,
            "snippet": snippet,
            "from_id": source_id,
            "to_id": target_id,
            "from_type": source_entity_type,
            "to_type": target_entity_type,
            "relationship_type": relationship_type,
        }
        relationships.append(relationship_entry)
    except json.JSONDecodeError as e:
      relationships = []

    print(f"\n\nentities:\n{entities}\n\nrelationships:\n{relationships}\n\n")
    return {
        "entities": entities,
        "relationships": relationships,
    }

  def add_entity(self, entity_type, data):
    relation_name = entity_type.lower()
    type_id = TypeID(prefix=relation_name)
    entity_id = str(type_id)
    # Update in-memory graph
    if entity_type not in self.graph["entities"]:
      self.graph["entities"][entity_type] = {}
    self.graph["entities"][entity_type][entity_id] = data
    # Update NexusDB
    actual_data = data["data"]
    relation = f"{relation_prefix}_{entity_type}"

    # Dynamically extract all fields and their values from actual_data
    fields = ["id"] + list(actual_data.keys())
    values = [[entity_id] +
              [actual_data[field] for field in fields if field != "id"]]

    print(f"name: {actual_data.get('name', '')}")
    print(f"description: {actual_data.get('description', '')}")
    print(f"actual_data: {actual_data}")

    print(
        f"\nInserting into NexusDB: {relation} with fields: {fields} and values: {values}\n\n"
    )
    self.nexus_db.insert(relation, fields, values)

    return entity_id

  def update_entity(self, entity_type, entity_id, data):
    entities = self.graph["entities"].get(entity_type)
    if entities and entity_id in entities:
      entities[entity_id].update(data)
      # Update NexusDB
      actual_data = data[
          "data"]  # Assuming 'data' has a 'data' key with the actual update data
      relation = f"{relation_prefix}_{entity_type}"

      # Dynamically prepare fields and values for the update operation
      fields = list(actual_data.keys())
      values = [[actual_data[key] for key in fields]]

      # Since it's an update, prepend 'id' to fields and the actual entity_id to each row of values
      fields.insert(0, "id")
      for row in values:
        row.insert(0, entity_id)
      self.nexus_db.update(relation, fields, values)
      return True
    return False

  def add_relationship(self, data):
    print(f"Adding relationship: {data}")
    try:
      relationship = data["relationship"].strip()

      # Prepare the data for NexusDB schema
      fields = [
          "relationship",
          "sourceId",
          "targetId",
          "sourceName",
          "targetName",
      ]
      values = [[
          relationship,
          data["from_id"],
          data["to_id"],
          data["from_entity"],
          data["to_entity"],
      ]]

      # Update NexusDB
      print("\n\n values: ", values, "\n\n")
      print(
          f"Inserting into NexusDB: relation={graph_relation}, fields={fields}, values={values}"
      )
      self.nexus_db.upsert(graph_relation, fields, values)

    except Exception as e:
      print(f"Error adding relationship: {e}")
      return False

    # Update in-memory graph
    self.graph["relationships"].append(data)

    return len(self.graph["relationships"])

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

      # Update NexusDB
      relation = f"{relation_prefix}_{entity_type.title()}"
      print(f"Deleting from NexusDB: {relation} where id = {entity_id}")

      relation_delete_condition = f"id = '{entity_id}'"
      relation_response = self.nexus_db.delete(relation,
                                               relation_delete_condition)

      target_condition = f"targetId = '{entity_id}'"
      target_response = self.nexus_db.delete(graph_relation, target_condition)

      source_condition = f"sourceId = '{entity_id}'"
      source_response = self.nexus_db.delete(graph_relation, source_condition)

      print(f"relation_response: {relation_response}")
      print(f"target_response: {target_response}")
      print(f"source_response: {source_response}")
      return True
    return False
