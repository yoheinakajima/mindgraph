import os
from neo4j import GraphDatabase
from .base import DatabaseIntegration

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")


# rename dict keys containing spaces with _
def remove_spaces(data):
    normalized_data = {}

    for key in data:
        val = data[key]

        if " " in key:
            key = key.replace(" ", "_")

        normalized_data[key] = val

    return normalized_data


class Neo4jDBIntegration(DatabaseIntegration):
    def __init__(self, schema_file_path="schema.json"):
        # Connect to Neo4j
        self._driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )

    def add_entity(self, entity_type, data):
        data["data"] = remove_spaces(data["data"])

        q = f"""CREATE (n:{entity_type})
                SET n = $attr
                RETURN elementId(n) AS id"""

        result = self._query(q, {"attr": data["data"]})

        # return entity ID
        return result[0]["id"]

    def get_full_graph(self):
        graph = {
            "entities": {},
            "relationships": [],
        }

        # get nodes
        nodes = self._query(
            "MATCH (n) RETURN n, elementId(n) AS id, labels(n)[0] AS label"
        )
        for node in nodes:
            lbl = node["label"]
            id = node["id"]
            node_props = node["n"]

            if lbl not in graph["entities"]:
                graph["entities"][lbl] = {}

            graph["entities"][lbl][id] = {"entity_type": lbl, "data": node_props}

        # get edges
        results = self._query(
            """
                              MATCH (src)-[e]->(dest)
                              RETURN elementId(src) AS src_id,
                                     labels(src)[0] AS from_type,
                                     type(e) AS relationship,
                                     elementId(dest) AS dest_id,
                                     labels(dest)[0] AS to_type
                              """
        )
        for row in results:
            desc = {
                "relationship": row["relationship"],
                "snippet": row["relationship"],
                "from_id": row["src_id"],
                "to_id": row["dest_id"],
                "from_type": row["from_type"],
                "to_type": row["to_type"],
                "from_entity": "",
                "to_entity": "",
                "relationship_type": row["relationship"],
            }

            graph["relationships"].append(desc)

        return graph

    def get_entity(self, entity_type, entity_id):
        q = f"""MATCH (n:{entity_type})
                WHERE elementId(n) = $id
                RETURN n"""

        result = self._query(q, {"id": entity_id})
        if len(result) == 1:
            return result[0]["n"]

        return {}

    def get_all_entities(self, entity_type):
        entities = {}

        q = f"MATCH (n:{entity_type}) RETURN n, elementId(n) AS id"

        result = self._query(q)
        for row in result:
            entities[row["id"]] = row["n"]

        return entities

    def update_entity(self, entity_type, entity_id, data):
        data["data"] = remove_spaces(data["data"])

        q = f"""MATCH (n:{entity_type})
                WHERE elementId(n) = $id
                SET n = $attr"""

        result = self._query(q, {"id": entity_id, "attr": data["data"]})

        return True

    def delete_entity(self, entity_type, entity_id):
        q = f"""MATCH (n:{entity_type})
                WHERE elementId(n) = $id
                DELETE n"""

        result = self._query(q, {"id": entity_id})

        return True

    def add_relationship(self, data):
        src_id = data["from_id"]
        dst_id = data["to_id"]
        edge_type = data["relationship"].strip().replace(" ", "_")
        src_entity = data["from_entity"]
        dst_entity = data["to_entity"]

        q = f"""MATCH (src), (dest)
                WHERE elementId(src) = $src_id AND elementId(dest) = $dest_id
                CREATE (src)-[:{edge_type}]->(dest)"""

        result = self._query(q, {"src_id": src_id, "dest_id": dst_id})

        return True

    def search_entities(self, search_params):
        search_params = remove_spaces(search_params)

        filters = " AND ".join([f"n.{key} = ${key}" for key in search_params])
        q = f"""MATCH (n)
                WHERE {filters}
                RETURN n, labels(n)[0] AS label, elementId(n) AS id"""

        nodes = self._query(q, search_params)
        results = []
        for n in nodes:
            results.append({"type": n["label"], "id": n["id"], **n["n"]})

        return results

    def search_entities_with_type(self, entity_type, search_params):
        search_params = remove_spaces(search_params)

        filters = " AND ".join([f"n.{key} = ${key}" for key in search_params])
        q = f"""MATCH (n:{entity_type})
                WHERE {filters}
                RETURN n, labels(n)[0] AS label, elementId(n) AS id"""

        nodes = self._query(q, search_params)

        results = []
        for n in nodes:
            results.append({"type": n["label"], "id": n["id"], **n["n"]})

        return results

    def search_relationships(self, search_params):
        search_params = remove_spaces(search_params)

        filters = " AND ".join([f"e.{key} = ${key}" for key in search_params])

        q = f"""MATCH (n)-[e]->()
               WHERE {filters}
               RETURN type(e) AS type"""

        edges = self._query(q, search_params)

        return [e["type"] for e in edges]

    def _query(self, cypher, params={}):
        with self._driver.session(database=NEO4J_DATABASE) as session:
            data = session.run(cypher, params)
            json_data = [r.data() for r in data]
            return json_data
