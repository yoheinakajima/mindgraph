# This Flask integration, `conditional_entity_addition`, uses OpenAI to conditionally add entities to a knowledge graph, 
# ensuring no duplicates are created based on the entity's data content. It interfaces with the application's model layer 
# to search existing entities and decide on new additions.

# First, the function checks for an 'entity_type' in the provided data, returning an error if it's missing. It then extracts 
# 'entity_data' from the data payload for search purposes.

# It conducts a search within the knowledge graph for each piece of entity data provided, aiming to find any potential 
# matches. This search is sensitive to string values, looking for partial matches.

# The search results are consolidated, ensuring unique entries are considered for comparison against the new entity data.

# The function prepares a message for the OpenAI API, articulating a task to determine if the new entity data matches any 
# of the search results, considering variations in name matching and additional entity details for a robust comparison.

# An OpenAI ChatCompletion call is made with the constructed message, with the AI tasked to return an entity ID if a match 
# is found or indicate 'No Matches' otherwise.

# Based on the AI's response, the function either adds the new entity to the knowledge graph (if no matches are found) and 
# returns a success response including the new entity's ID, or it returns a response indicating a match was found with the 
# matched entity's ID.

# Error handling is included to catch and report issues during the OpenAI API call process.

# Finally, a `register` function is provided to make `conditional_entity_addition` available within the application's 
# integration manager, allowing it to be dynamically loaded and invoked as part of the application's integration ecosystem.

# This integration highlights a sophisticated use of AI for data deduplication within web applications, ensuring data integrity 
# and reducing redundancy in knowledge graph construction and expansion.


# app/integrations/conditional_entity_addition.py
import os
import openai
from flask import jsonify
from app.models import search_entities_with_type, add_entity

# Your OpenAI API key should be securely stored and accessed. Hardcoding is not recommended for production systems.
openai.api_key = os.environ['OPENAI_API_KEY']
openai.base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')

OPENAI_MODEL_NAME = "gpt-4-turbo-preview"

def conditional_entity_addition(app, data):
    with app.app_context():
        # Retrieve the entity type from the data
        entity_type = data.get('entity_type', None)
        # If no entity type is provided, return an error
        if not entity_type:
            return jsonify({"error": "Entity type is required."}), 400
  
        # Adjusted to access nested 'data'
        entity_data = data.get('data', {})
        search_results = []
  
        # Run a search for each parameter in the input data
        for key, value in entity_data.items():
            # Ensure only strings are searched with a partial match
            if isinstance(value, str):
                search_params = {key: value}
                print(f"Search parameters: {search_params}")
                print("entity type: ", entity_type)
                results = search_entities_with_type(entity_type, search_params)
                print(f"Search results: {results}")
                search_results.extend(results)
  
        # Combine all search results
        combined_results = {result['id']: result for result in search_results}.values()
        print(f"Combined results: {list(combined_results)}")

        # Prepare the message for OpenAI API
        messages = [
            {"role": "system", "content": "You are a helpful assistant who's specialty is to decide if new input data matches data already in our database. Review the search results provided, compare against the input data, and if there's a match respond with the ID number of the match, and only the ID number. If there are no matches, respond with 'No Matches'. Your response is ALWAYS an ID number alone, or 'No Matches'. When reviewing whether a match existings in our search results to our new input, take into account that the name may not match perfectly (for example, one might have just a first name, or a nick name, while the other has a full name), in which case look at the additional information about the user to determine if there's a strong likelihood they are the same person. For companies, you should consider different names of the same company as the same, such as EA and Electronic Arts (make your best guess). If the likelihood is strong, respond with and only with the ID number. If likelihood is low, respond with 'No Matches'."},
          {"role": "user", "content": f"Here are the search results: {list(combined_results)}. Does any entry match the input data: {data}?"}
        ]

        # Make a call to OpenAI API
        try:
            response = openai.ChatCompletion.create(
                model=os.environ.get('OPENAI_MODEL_NAME', OPENAI_MODEL_NAME),
                messages=messages
            )
            ai_response = response.choices[0].message.content.strip()
            print(f"AI response: {ai_response}")

            # Process the AI's response
            if "no matches" in ai_response.lower():
                # If no match found, add the new entity
                entity_id = add_entity(entity_type, data)
                return jsonify({"success": True, "entity_id": entity_id}), 200
            else:
                # If a match is found, return the match details
                match_id = ai_response
                return jsonify({"success": False, "message": "Match found", "match_id": match_id}), 200

        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return jsonify({"error": str(e)}), 500

def register(integration_manager):
    integration_manager.register('conditional_entity_addition', conditional_entity_addition)
