import os
import openai
from flask import jsonify
import json
from app.models import get_full_graph, search_entities, search_relationships

openai.api_key = os.getenv('OPENAI_API_KEY')


def collect_connections(nodes, edges):
  graph = get_full_graph()
  triplets = []

  # First, directly process the edges to construct triplets for these specific relationships
  for edge in edges:
      from_id = edge['from_temp_id']
      to_id = edge['to_temp_id']
      # Attempt to retrieve the relationship's description directly, or construct a fallback description
      relationship_desc = edge.get('data', {}).get('snippet', f'Unknown relationship from {from_id} to {to_id}')
      triplets.append(relationship_desc)

  # Create a set of node temp IDs from the input nodes for quick lookup
  node_temp_ids = {node['temp_id'] for node in nodes}

  # Then, for each node in the input list, use find_connected_triplets to find all additional triplets
  for node in nodes:
      node_temp_id = node['temp_id']
      additional_triplets = find_connected_triplets(node_temp_id, graph)
      triplets.extend(additional_triplets)

  return triplets

def find_connected_triplets(node_id, graph, exclude_id=None):
    """
    Find all triplets for a given node except those connected to exclude_id.
    """
    connected_triplets = []
    for relationship in graph['relationships']:
        # Check if the relationship involves the node in question and is not excluded
        if (relationship['from_id'] == node_id and relationship['to_id'] != exclude_id) or (relationship['to_id'] == node_id and relationship['from_id'] != exclude_id):
            # Construct the triplet description using the snippet or a default format
            from_node_name = next((node['data']['name'] for entity_type, entities in graph['entities'].items() for _, node in entities.items() if node['data']['temp_id'] == relationship['from_id']), 'Unknown')
            to_node_name = next((node['data']['name'] for entity_type, entities in graph['entities'].items() for _, node in entities.items() if node['data']['temp_id'] == relationship['to_id']), 'Unknown')
            relationship_type = relationship.get('relationship', 'connected to')
            triplet = f"{from_node_name} {relationship_type} {to_node_name}" if 'snippet' not in relationship else relationship['snippet']
            print(triplet)
            connected_triplets.append(triplet)
    
    return connected_triplets




def generate_search_parameters(input_text):
  try:
      response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
              {"role": "system", "content": """You are a helpful assistant expected to generate search parameters in an array format for entities and relationships based on the given user input. Output should be in array format that looks like this with "name" as the key for every parameter. User: Did Johnny Appleseed plant apple seeds? Assistant:{"name":"John","name":"Appleseed","name":"Apple","name":"Seed"}."""},
              {"role": "user", "content": f"User input:{input_text}"}
          ],
          #response_format={"type": "json_object"}
      )
      search_parameters = response.choices[0].message['content']
      print("search_para: ", search_parameters)
      return json.loads(search_parameters)
  except Exception as e:
      print(f"Error generating search parameters: {e}")
      return []


def ai_search(app, input_text):
  print("ai_search start")
  with app.app_context():
      # Assuming generate_search_parameters now correctly formats the input for search
      search_parameters = generate_search_parameters(input_text)
      print("search_parameters" , search_parameters)
      if not search_parameters:
          return jsonify({"error": "Failed to generate search parameters"}), 400

      graph = get_full_graph()
      entity_results = []
      relationship_results = []

      # Iterate through each dictionary in the list of dictionaries
      for param in search_parameters:
          # Assuming each dictionary in the list has only one key-value pair you want to use
          for key, value in param.items():
              param_dict = {key: value}
              print(f"param_dict: {param_dict}")
              entity_results.extend(search_entities(param_dict))
              relationship_results.extend(search_relationships(param_dict))
  

      print("entity_results: ", entity_results)
      print("relationship_results: ", relationship_results)
      # Now expecting a single list of triplets instead of two separate lists
      triplets = collect_connections(entity_results, relationship_results)
      print("triplet: ", triplets)

      # Construct a message to send to GPT based on triplets
      if triplets:
          message = f"Based on the user input '{input_text}', here are the relationships found: {', '.join(triplets)}. Generate an insightful response."
      else:
          message = f"Based on the user input '{input_text}', no specific relationships were found. Generate a general insight."

      print("message: ", message)

      try:
          response = openai.ChatCompletion.create(
              model="gpt-3.5-turbo",
              messages=[
                  {"role": "system", "content": "You're an assistant that generates a concise answer to the uer input based on the data provided following the user input."},
                  {"role": "user", "content": message}
              ]
          )
          # Assuming the model's response is directly usable
          answer = response.choices[0].message['content']
          print("answer: ", answer)
          return jsonify({"answer": answer, "triplets":str(triplets)}), 200
      except Exception as e:
          print(f"Error processing AI search: {e}")
          return jsonify({"error": str(e)}), 500

def register(integration_manager):
    integration_manager.register('ai_search', ai_search)
