# This Flask integration, `conditional_relationship_addition`, utilizes OpenAI for intelligently determining whether 
# to add a new relationship to a knowledge graph, based on a comparison with existing relationships. It interacts with 
# the application's model layer for searching and adding relationships.

# Initially, it verifies the presence of necessary identifiers ('from_id', 'from_type', 'to_id', 'to_type') in the provided data, 
# returning an error for any missing field.

# It then compiles search parameters from the data, specifically targeting identifiers that define a relationship, and 
# performs a search using `search_relationships` to find any existing relationships that match these parameters.

# A message is prepared for the OpenAI API, detailing the task of comparing the proposed relationship against existing ones 
# in the database. The assistant is instructed to consider a relationship a match only if all parameters exactly correspond 
# to an existing entry, responding with either the full details of the matching relationship as JSON or 'No Matches'.

# An OpenAI ChatCompletion call is made with this message, and the AI's response is processed. If the AI indicates 'No Matches', 
# indicating that the proposed relationship does not exist in the database, the new relationship is added through 
# `add_relationship` and a success response is returned. If a match is found, the function returns a response detailing 
# the matched relationship.

# Error handling is incorporated to manage and report any issues encountered during the OpenAI API call.

# Additionally, a `register` function is included to ensure the `conditional_relationship_addition` integration is available 
# within the application's integration manager. This allows for dynamic loading and invocation within the application's 
# integration framework.

# This integration showcases an advanced application of AI to enhance data integrity within web applications, enabling 
# precise and automated management of relationships in a knowledge graph, and preventing the duplication of relationship data.



# app/integrations/conditional_relationship_addition.py
import os
import openai
from flask import jsonify
from app.models import search_relationships, add_relationship

# Your OpenAI API key should be securely stored and accessed. Hardcoding is not recommended for production systems.
openai.api_key = os.environ['OPENAI_API_KEY']
openai.base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')

OPENAI_MODEL_NAME = "gpt-4-turbo-preview"

def conditional_relationship_addition(app, data):
    with app.app_context():
        # Validate that we have all necessary identifiers for a relationship
        required_fields = ['from_id', 'from_type', 'to_id', 'to_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"'{field}' is required."}), 400

        # Prepare search parameters, excluding 'relationship_type' if not provided
        search_params = {key: data[key] for key in required_fields}

        print(f"Search parameters: {search_params}")
        search_results = search_relationships(search_params)

        # Prepare the message for OpenAI API
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Your task is to determine whether a proposed new relationship between two nodes already exists in the database. You should only consider a relationship a match if all the search parameters correspond exactly to an existing relationship. If you find a match, your response should be the full details of the matching relationship, and only the full details as JSON. If there is no match, respond with 'No Matches'. Your response should always be either just JSON response or 'No Matches'."},
            {"role": "user", "content": f"Existing relationships: {search_results}. Do any of these match the proposed relationship details: {data}?"}
        ]

        # Make a call to OpenAI API
        try:
            response = openai.ChatCompletion.create(
                model=os.environ.get('OPENAI_MODEL_NAME', OPENAI_MODEL_NAME),
                messages=messages
            )
            ai_response = response.choices[0].message.content.strip()

            # Process the AI's response
            if "No Matches" in ai_response:
                # If no match found, add the new relationship
                relationship_id = add_relationship(data)
                return jsonify({"success": True, "relationship": data}), 200
            else:
                # If a match is found, return the matched relationship data
                return jsonify({"success": False, "message": "Match found", "matching_relationship": ai_response}), 200

        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return jsonify({"error": str(e)}), 500

def register(integration_manager):
    integration_manager.register('conditional_relationship_addition', conditional_relationship_addition)
