import os
from falkordb import FalkorDB

from .base import DatabaseIntegration

FALKOR_HOST     = os.environ.get("FALKOR_HOST", "127.0.0.1")
FALKOR_PORT     = os.environ.get("FALKOR_PORT", 6379)
FALKOR_GRAPH_ID = os.environ.get("FALKOR_GRAPH_ID", "mindgraph")

# rename dict keys containing spaces with _
def remove_spaces(data):
    normalized_data = {}

    for key in data:
        val = data[key]

        if ' ' in key:
            key = key.replace(' ', '_')

        normalized_data[key] = val

    return normalized_data

class FalkorDBIntegration(DatabaseIntegration):
    def __init__(self, schema_file_path="schema.json"):
        # Connect to FalkorDB
        self.db = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)
        self.g  = self.db.select_graph(FALKOR_GRAPH_ID)

    def add_entity(self, entity_type, data):
        data['data'] = remove_spaces(data['data'])

        q = f"""CREATE (n:{entity_type})
                SET n = $attr
                RETURN ID(n)"""

        result = self.g.query(q, {'attr': data["data"]}).result_set

        # return entity ID
        return result[0][0]

    def get_full_graph(self):
        graph = {
            "entities": {},
            "relationships": [],
        }

        # get nodes
        nodes = self.g.query("MATCH (n) RETURN n").result_set
        for node in nodes:
            node = node[0]
            lbl = node.labels[0]

            if lbl not in graph['entities']:
                graph['entities'][lbl] = {}

            graph['entities'][lbl][node.id] = {'entity_type': lbl, 'data': node.properties}

        # get edges
        results = self.g.query("MATCH (src)-[e]->(dest) RETURN src, e, dest").result_set
        for row in results:
            src  = row[0]
            e    = row[1]
            dest = row[2]

            desc = {
                    "relationship": e.relation,
                    "snippet": e.relation,
                    "from_id": src.id,
                    "to_id": dest.id,
                    "from_type": src.labels[0],
                    "to_type": dest.labels[0],
                    "from_entity": '',
                    "to_entity": '',
                    "relationship_type": e.relation
                    }

            graph['relationships'].append(desc)

        return graph

    def get_entity(self, entity_type, entity_id):
        q = f"""MATCH (n:{entity_type})
                WHERE ID(n) = $id
                RETURN n"""

        result = self.g.query(q, {'id': entity_id}).result_set
        if len(result) == 1:
            n = result[0][0]
            return n.properties

        return {}

    def get_all_entities(self, entity_type):
        entities = {}

        q = f"MATCH (n:{entity_type}) RETURN n"

        result = self.g.query(q).result_set
        for row in result:
            n = row[0]
            entities[n.id] = n.properties

        return entities

    def update_entity(self, entity_type, entity_id, data):
        data['data'] = remove_spaces(data['data'])

        q = f"""MATCH (n:{entity_type})
                WHERE ID(n) = $id
                SET n = $attr"""

        result = self.g.query(q, {'id': entity_id, 'attr': data['data']})

        return result.properties_set > 0 or result.properties_removed > 0

    def delete_entity(self, entity_type, entity_id):
        q = f"""MATCH (n:{entity_type})
                WHERE ID(n) = $id
                DELETE n"""

        result = self.g.query(q, {'id': entity_id})

        return (result.nodes_deleted == 1)

    def add_relationship(self, data):
        src_id     = int(data["from_id"])
        dst_id     = int(data["to_id"])
        edge_type  = data["relationship"].strip().replace(' ', '_')
        src_entity = data["from_entity"]
        dst_entity = data["to_entity"]

        q = f"""MATCH (src), (dest)
                WHERE ID(src) = $src_id AND ID(dest) = $dest_id
                CREATE (src)-[:{edge_type}]->(dest)"""

        result = self.g.query(q, {'src_id': src_id, 'dest_id': dst_id})

        return result.relationships_created == 1

    def search_entities(self, search_params):
        search_params = remove_spaces(search_params)

        filters = " AND ".join([f"n.{key} = ${key}" for key in search_params])
        q = f"""MATCH (n)
                WHERE {filters}
                RETURN n"""
        
        nodes = self.g.query(q, search_params).result_set

        results = []
        for n in nodes:
            n = n[0]
            results.append({"type": entity_type, "id": n.id, **n.properties})

        return results

    def search_entities_with_type(self, entity_type, search_params):
        search_params = remove_spaces(search_params)

        filters = " AND ".join([f"n.{key} = ${key}" for key in search_params])
        q = f"""MATCH (n:{entity_type})
                WHERE {filters}
                RETURN n"""
        
        nodes = self.g.query(q, search_params).result_set

        results = []
        for n in nodes:
            n = n[0]
            results.append({"type": entity_type, "id": n.id, **n.properties})

        return results

    def search_relationships(self, search_params):
        search_params = remove_spaces(search_params)

        filters = " AND ".join([f"e.{key} = ${key}" for key in search_params])

        q = f"""MATCH (n)-[e]->()
               WHERE {filters}
               RETURN e"""

        edges = self.g.query(q, search_params).result_set

        return [e[0] for e in edges]

