import ctypes
import json
import os
import time

from nebula3.gclient.net import ConnectionPool
from nebula3.gclient.net.SessionPool import SessionPool
from nebula3.Config import Config, SessionPoolConfig

from .base import DatabaseIntegration
from .memory import InMemoryDatabase


NEBULA_USER = os.environ.get("NEBULA_USER", "root")
NEBULA_PASSWORD = os.environ.get("NEBULA_PASSWORD", "nebula")
NEBULA_ADDRESS = os.environ.get("NEBULA_ADDRESS", "127.0.0.1:9669")
NEBULA_SPACE = os.environ.get("NEBULA_SPACE", "mindgraph")
NEBULA_SPACE_PARTITIONS = os.environ.get("NEBULA_SPACE_PARTITIONS", 1)
NEBULA_SPACE_REPLICAS = os.environ.get("NEBULA_SPACE_REPLICAS", 1)
NEBULA_DDL_WAIT_BACKOFF_SECONDS = os.environ.get("NEBULA_DDL_WAIT_BACKOFF_SECONDS", 15)
NEBULA_DDL_WAIT_RETRIES = os.environ.get("NEBULA_DDL_WAIT_RETRIES", 3)
NEBULA_GRAPH_SAMPLE_SIZE = os.environ.get("NEBULA_GRAPH_SAMPLE_SIZE", 2000)


def murmur64(string: str, seed: int = 0xC70F6907) -> int:
    """
    MurmurHash3 64-bit implementation. Same as the one used in NebulaGraph.

    This is needed as MindGraph is using numeric IDs for entities.

    In NebulaGraph, the built-in hash function is used to hash the vertex ID when
    Vertex ID Type is int64.

    Query `RETURN hash("foobar")` in Nebula Console to see
    the hash value of a string.

    Args:
        string (str): The string to hash.
        seed (int): The seed value.

    Returns:
        int: The 64-bit hash value.
    """
    data = bytes(string, encoding="utf8")

    def bytes_to_long(bytes):
        assert len(bytes) == 8
        return sum((b << (k * 8) for k, b in enumerate(bytes)))

    m = ctypes.c_uint64(0xC6A4A7935BD1E995).value

    r = ctypes.c_uint32(47).value

    MASK = ctypes.c_uint64(2**64 - 1).value

    data_as_bytes = bytearray(data)

    seed = ctypes.c_uint64(seed).value

    h = seed ^ ((m * len(data_as_bytes)) & MASK)

    off = int(len(data_as_bytes) / 8) * 8
    for ll in range(0, off, 8):
        k = bytes_to_long(data_as_bytes[ll : ll + 8])
        k = (k * m) & MASK
        k = k ^ ((k >> r) & MASK)
        k = (k * m) & MASK
        h = h ^ k
        h = (h * m) & MASK

    l = len(data_as_bytes) & 7

    if l >= 7:
        h = h ^ (data_as_bytes[off + 6] << 48)

    if l >= 6:
        h = h ^ (data_as_bytes[off + 5] << 40)

    if l >= 5:
        h = h ^ (data_as_bytes[off + 4] << 32)

    if l >= 4:
        h = h ^ (data_as_bytes[off + 3] << 24)

    if l >= 3:
        h = h ^ (data_as_bytes[off + 2] << 16)

    if l >= 2:
        h = h ^ (data_as_bytes[off + 1] << 8)

    if l >= 1:
        h = h ^ data_as_bytes[off]
        h = (h * m) & MASK

    h = h ^ ((h >> r) & MASK)
    h = (h * m) & MASK
    h = h ^ ((h >> r) & MASK)

    return ctypes.c_longlong(h).value


class NebulaGraphIntegration(InMemoryDatabase, DatabaseIntegration):
    def __init__(self, schema_file_path="schema.json"):
        self.nebula_user = NEBULA_USER
        self.nebula_password = NEBULA_PASSWORD
        self.nebula_address = NEBULA_ADDRESS
        self.nebula_space = NEBULA_SPACE

        self.nebula_connection = ConnectionPool()
        self.client = None
        self._ensure_nebula_connection()

        self.schema = self._load_schema(schema_file_path)
        self._ensure_nebulagraph_schema()
        # cache and fast track implementation for search_entities
        self.graph = {"entities": {}, "relationships": []}

    def _ensure_nebula_connection(self):
        # Ensure a connection to Nebula Graph is established
        try:
            address, port = self.nebula_address.split(":")
            config = Config()
            assert self.nebula_connection.init(
                [(address, int(port))], config
            ), "Failed to connect to NebulaGraph"
            session = self.nebula_connection.get_session(
                self.nebula_user, self.nebula_password
            )
            result = session.execute(
                f"CREATE SPACE IF NOT EXISTS {self.nebula_space} "
                f"(vid_type=int64, partition_num={NEBULA_SPACE_PARTITIONS}, "
                f"replica_factor={NEBULA_SPACE_REPLICAS});"
            )
        except Exception as e:
            print(f"Error establishing NebulaGraph connection: {e}")
            raise e

        assert result, "Failed to create space in NebulaGraph"

        # Await for the space to be created
        try:
            retries = int(NEBULA_DDL_WAIT_RETRIES)
            backoff_seconds = int(NEBULA_DDL_WAIT_BACKOFF_SECONDS)
            use_space = None
            for attempt in range(retries):
                try:
                    use_space = session.execute(f"USE {self.nebula_space}")
                    if use_space.is_succeeded():
                        break
                    else:
                        raise Exception(
                            f"Failed to use space {self.nebula_space}: {use_space.error_msg()}"
                        )
                except Exception as e:
                    if attempt < retries - 1:  # i.e., 0 or 1 for 3 retries
                        print(
                            f"Attempt {attempt + 1} failed with error: {e}. Retrying..."
                        )
                        time.sleep(
                            backoff_seconds * 2**attempt
                        )  # Exponential backoff
                    else:
                        print(f"All attempts to use space {self.nebula_space} failed.")
            if not use_space or use_space.is_succeeded() is False:
                print(f"Failed to use space {self.nebula_space}.")
                raise Exception(f"Failed to use space {self.nebula_space}.")
        except Exception as e:
            print(f"Error using space: {e}")
            raise e
        finally:
            try:
                session.release()
            except Exception as e:
                print(f"Error releasing session: {e}")

        self.client = SessionPool(
            self.nebula_user,
            self.nebula_password,
            self.nebula_space,
            self.nebula_connection._addresses,
        )
        self.client.init(SessionPoolConfig())

    def _load_schema(self, schema_file_path):
        # Load and return the schema from the schema.json file
        with open(schema_file_path, "r") as file:
            schema = json.load(file)
        return schema

    def _get_nebula_schema(self):
        tags_raw = self.client.execute("SHOW TAGS").column_values("Name")
        tags = [tag.cast() for tag in tags_raw]
        edges_raw = self.client.execute("SHOW EDGES").column_values("Name")
        edges = [edge.cast() for edge in edges_raw]
        return {"entities": tags, "relationships": edges}

    def _ensure_nebulagraph_schema(self):
        """
        Ensure the NebulaGraph schema is up to date with the expected schema.

        We map MindGraph Schema to NebulaGraph Schema(Property Graph) as follows:

        We use NebulaGraph VERTEX TAG to represent the entity type in MindGraph.
        - The schema per all TAGs is the same, which is with properties named "name" and "description".
        - The Vertex ID is int typed and hashed from its name.
        We use NebulaGraph EDGE TYPE to represent the relationship type in MindGraph.
        - The schema per all EDGEs is the same, which is with a single property named "snippet".

        Note, for relationship extraction there is a fallback type: "associated" which is used when no type is provided.

        """
        # Build Schema Creation Queries
        # VERTEX TAGS
        tag_names = []
        tag_queries = []
        relationships_in_schema = set()
        for entity_type, entity_item in self.schema.items():
            tag_name = entity_type
            tag_queries.append(
                f"CREATE TAG IF NOT EXISTS `{tag_name}`(name string, description string);"
            )
            tag_names.append(tag_name)
            for relationship_type in entity_item.get("edge_types", {}).keys():
                relationships_in_schema.add(relationship_type)
        # EDGES TYPES
        edge_names = []
        edge_queries = []
        for relationship_type in relationships_in_schema:
            edge_name = relationship_type
            edge_queries.append(
                f"CREATE EDGE IF NOT EXISTS `{edge_name}`(snippet string, relationship_type string);"
            )
            edge_names.append(edge_name)

        current_schema = self._get_nebula_schema()
        missing_tags = set(tag_names) - set(current_schema["entities"])
        missing_edges = set(edge_names) - set(current_schema["relationships"])

        if missing_tags or missing_edges:
            print(
                f"Missing Schema will be created:\ntags: {missing_tags}\nedges: {missing_edges}"
            )

            try:
                # Execute Schema Creation Queries
                query = "\n".join(tag_queries + edge_queries)
                execute_result = self.client.execute(query)
                assert (
                    execute_result.is_succeeded()
                ), f"Failed to create tags and edges: {execute_result.error_msg()}\n query: {query}"
            except Exception as e:
                print(f"Error creating tags and edges: {e}")
                raise e
            else:
                print(f"Successfully created tags and edges: {query}")

    def get_full_graph(self, limit=NEBULA_GRAPH_SAMPLE_SIZE):
        """
        Return the sampled full graph. sample size is configurable with NEBULA_GRAPH_SAMPLE_SIZE.

        Returns:
            dict: The full graph.
        """
        graph_sample = {
            "entities": {},
            "relationships": [],
        }
        vector_id_map = {}
        next_id = 0

        # Get edges
        edges = self.client.execute(
            f"MATCH ()-[e]->() RETURN e LIMIT {limit} ;"
        ).column_values("e")
        vertex_ids = set()

        for edge_raw in edges:
            edge = edge_raw.cast()
            data_raw = edge.properties()
            data = {k: v.cast() for k, v in data_raw.items()}
            data.update(
                {
                    "relationship": edge.edge_name(),
                    "from_id": edge.start_vertex_id().cast(),
                    "to_id": edge.end_vertex_id().cast(),
                    "from_entity": "",
                    "to_entity": "",
                }
            )
            graph_sample["relationships"].append(data)
            vertex_ids.add(edge.start_vertex_id().cast())
            vertex_ids.add(edge.end_vertex_id().cast())

        # Get vertices
        vertices_id_str = ", ".join(str(v) for v in vertex_ids)
        vertices = self.client.execute(
            f"MATCH (v) WHERE id(v) IN [{vertices_id_str}] RETURN v;"
        ).column_values("v")

        for vertex_raw in vertices:
            vertex = vertex_raw.cast()
            for tag in vertex.tags():
                entity_type = tag
                entity_id = vertex.get_id().cast()
                entity_id = entity_id
                data_raw = vertex.properties(tag)
                data = {k: v.cast() for k, v in data_raw.items()}
                temp_id = int(next_id)
                vector_id_map[entity_id] = {
                    "temp_id": next_id,
                    "name": data.get("name", f"{entity_type}_{entity_id}"),
                }
                next_id += 1
                data["temp_id"] = temp_id
                record = {"entity_type": entity_type, "data": data}
                if tag in graph_sample["entities"]:
                    graph_sample["entities"][entity_type][temp_id] = record
                else:
                    graph_sample["entities"][entity_type] = {temp_id: record}

        # update from entity and to entity with entity name
        for relationship in graph_sample["relationships"]:
            from_id = relationship["from_id"]
            to_id = relationship["to_id"]
            relationship["from_entity"] = vector_id_map.get(from_id, {}).get("name", "")
            relationship["to_entity"] = vector_id_map.get(to_id, {}).get("name", "")
            temp_from_id = vector_id_map.get(from_id, {}).get("temp_id", "")
            temp_to_id = vector_id_map.get(to_id, {}).get("temp_id", "")
            relationship["from_id"] = temp_from_id
            relationship["to_id"] = temp_to_id

        return graph_sample

    def _get_cache_full_graph(self, limit=NEBULA_GRAPH_SAMPLE_SIZE, force=False):
        if force or not self.graph["entities"] or not self.graph["relationships"]:
            self.graph = self.get_full_graph(limit=limit)
        return self.graph

    def get_entity(self, entity_type, entity_id):
        """
        Get an entity from the graph.

        Args:
            entity_type (str): The type of entity.
            entity_id (str): The ID of the entity.

        Returns:
            dict: The entity.
        """
        result = self.client.execute(
            f"MATCH (v:`{entity_type}`) WHERE id(v) == {entity_id} RETURN v;"
        )
        if result.is_succeeded() and result.row_size() > 0:
            for vertex in result.column_values("v"):
                return vertex.properties(entity_type)
        return {}

    def get_all_entities(self, entity_type):
        """
        Get all entities of a given type.

        Args:
            entity_type (str): The type of entity.

        Returns:
            dict: The entities.
        """
        entities = {}
        result = self.client.execute(f"MATCH (v:`{entity_type}`) RETURN v;")
        if result.is_succeeded():
            for vertex in result:
                entity_id = vertex.get_id().cast()
                data = vertex.properties()
                entities[entity_id] = data
        return entities

    def add_entity(self, entity_type, data):
        """
        Add an entity to the graph.

        Args:
            entity_type (str): The type of entity.
            data (dict): The entity data.

        Returns:
            str: The ID of the new entity.

        example_type = 'person'
        example_data = {
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        """
        vertex_tag = entity_type

        actual_data = data["data"]
        prop_name = actual_data.get("name", "")
        if not prop_name:
            raise ValueError("Entity name is required.")
        prop_description = actual_data.get("description", "")
        vertex_id = murmur64(prop_name)

        # Insert into NebulaGraph
        query = f"INSERT VERTEX {vertex_tag}(name, description) VALUES {vertex_id}:('{prop_name}', '{prop_description}');"
        result = self.client.execute(query)
        assert result.is_succeeded(), f"Failed to insert vertex: {result.error_msg()}"

        # Added to cache
        if entity_type in self.graph["entities"]:
            self.graph["entities"][entity_type][vertex_id] = actual_data
        else:
            self.graph["entities"][entity_type] = {vertex_id: actual_data}

        return str(vertex_id)

    def update_entity(self, entity_type, entity_id, data):
        """
        Update an entity in the graph.

        Args:
            entity_type (str): The type of entity.
            entity_id (str): The ID of the entity.
            data (dict): The entity data to update.

        Returns:
            bool: True if the entity was updated, otherwise False.
        """

        # TODO: allow name to be updated, for now name is 1-1 with ID,
        # in the future we may want to allow name changes by intrducing a _name property

        # Now we just ensure the name is hashed to the same ID if name in data
        # compare entity_id and hased name, if different raise error
        # if no name field or name's hash is the same as entity_id, perform upsert directly

        actual_data = data["data"]
        prop_name = actual_data.get("name", "")
        if prop_name:
            vertex_id = murmur64(prop_name)
            if vertex_id != entity_id:
                raise ValueError("Entity name cannot be changed for now.")
        vertex_id = entity_id

        description = actual_data.get("description", "")
        if description:
            query = f"UPDATE VERTEX ON {entity_type} \"{vertex_id}\" SET description = '{description}' WHEN description != '{description}' YIELD description;"
            result = self.client.execute(query)
            if not result.is_succeeded():
                print(f"Failed to update vertex: {result.error_msg()}")
                return False
            # Update cache
            self.graph["entities"][entity_type][vertex_id].update(actual_data)
            return True
        return False

    def add_relationship(self, data):
        """
        Add a relationship to the graph.

        Args:
            data (dict): The relationship data.

        Returns:
            int: The number of relationships in the graph.

        example_data = {
            "relationship": "Works for",
            "relationship_type": "associated",
            "from_id": "1",
            "to_id": "2",
            "from_entity": "Person",
            "to_entity": "Organization",
        }
        """
        # Note, AS EDGE TYPE in NebulaGrpah don't enfource from/to entity types, we don't persist those information.
        # But if needed extra properties can be added to the edge type to store the entity types.
        print(f"Adding relationship: {data}")

        try:
            edge_type = data["relationship"].strip()
            src_id = int(data["from_id"])
            dst_id = int(data["to_id"])
            snippet = data["snippet"]
            # src_entity = data["from_entity"]
            # dst_entity = data["to_entity"]
            relationship_type = data.get("relationship_type", "associated")
            query = f"INSERT EDGE `{edge_type}`(snippet, relationship_type) VALUES {src_id} -> {dst_id}:('{snippet}', '{relationship_type}');"
            result = self.client.execute(query)
            assert result.is_succeeded(), f"Failed to insert edge: {result.error_msg()}"
        except Exception as e:
            print(f"Error adding relationship: {e}")
            raise e

        # Update cache
        self.graph["relationships"].append(data)

        return murmur64(f"{src_id}{edge_type}{dst_id}")

    def delete_entity(self, entity_type, entity_id):
        """
        Delete an entity from the graph.
        """

        # Ensure such entity exists

        result = self.client.execute(
            f"MATCH (v:`{entity_type}`) WHERE id(v) == {entity_id} RETURN v;"
        )
        assert result.is_succeeded(), f"Failed to find vertex: {result.error_msg()}"
        if result.row_size() == 0:
            return False

        # Get edges

        # Invovled vertices to be removed:

        invloved_vertices = []

        # (entity_id)-[]-(involved) but not (involved)-[]-(other_entities)

        invloved_vertices_raw = self.client.execute(
            f"GO FROM {entity_id} OVER * BIDIRECT YIELD DISTINCT id($$) AS associated_node "
            f"MINUS "
            f"(GO FROM {entity_id} OVER * BIDIRECT YIELD DISTINCT id($$) AS associated_node | "
            f"GO FROM $-.associated_node OVER * BIDIRECT "
            f"WHERE id($$) != {entity_id} YIELD DISTINCT $-.associated_node AS associated_node);"
        ).column_values("associated_node")

        if invloved_vertices_raw:
            invloved_vertices = [int(v.cast()) for v in invloved_vertices_raw]
            print(f"Invloved vertices: {invloved_vertices}")

            # Remove the entity and all its associated nodes
            # Remove the edges between the entity and its associated nodes

            vid_list_str = ", ".join(str(v) for v in invloved_vertices)

            result = self.client.execute(f"DELETE VERTEX {vid_list_str} WITH EDGE;")
            assert (
                result.is_succeeded()
            ), f"Failed to delete vertex: {result.error_msg()}"

        result = self.client.execute(f"DELETE VERTEX {entity_id} WITH EDGE;")
        assert result.is_succeeded(), f"Failed to delete vertex: {result.error_msg()}"

        # Update cache
        if (
            entity_type in self.graph["entities"]
            and entity_id in self.graph["entities"][entity_type]
        ):
            del self.graph["entities"][entity_type][entity_id]
        # Filter out relationships involving the deleted entity
        self.graph["relationships"] = [
            relationship
            for relationship in self.graph["relationships"]
            if relationship["from_id"] != entity_id
            and relationship["to_id"] != entity_id
        ]

        return True

    def search_entities(self, search_params):
        # TODO: Implement search_entities on NebulaGraph side
        self._get_cache_full_graph()
        results = []
        for entity_type, entities in self.graph["entities"].items():
            for entity_id, entity_details in entities.items():
                entity_info = entity_details.get("data", {})
                # Convert values to strings for comparison
                if all(
                    str(value).lower() in str(entity_info.get(key, "")).lower()
                    for key, value in search_params.items()
                ):
                    results.append(
                        {"type": entity_type, "id": entity_id, **entity_info}
                    )
        return results

    def search_entities_with_type(self, entity_type, search_params):
        # TODO: Implement search_entities on NebulaGraph side
        self._get_cache_full_graph()
        results = []
        for entity_id, entity_details in (
            self.graph["entities"].get(entity_type, {}).items()
        ):
            entity_info = entity_details.get("data", {})
            # Convert values to strings for comparison
            if all(
                str(value).lower() in str(entity_info.get(key, "")).lower()
                for key, value in search_params.items()
            ):
                results.append({"type": entity_type, "id": entity_id, **entity_info})
        return results

    def search_relationships(self, search_params):
        # TODO: Implement search_relationships on NebulaGraph side
        self._get_cache_full_graph()
        results = []
        for relationship in self.graph["relationships"]:
            # Convert values to strings for comparison
            if all(
                str(value).lower() in str(relationship.get(key, "")).lower()
                for key, value in search_params.items()
            ):
                results.append(relationship)
        return results
