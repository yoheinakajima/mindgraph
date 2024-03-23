from flask import jsonify, Flask
import requests
from bs4 import BeautifulSoup
from app.integration_manager import get_integration_function 
from urllib.parse import unquote

app = Flask(__name__)

def url_input(app, data):
    with app.app_context():
        encoded_url = data['natural_input']
        print("Encoded URL:", encoded_url)
        if not encoded_url:
            return jsonify({"error": "URL not provided"}), 400
  
        # Decode the URL
        url = unquote(encoded_url)
        print("Decoded URL:", url)

        try:
            response = requests.get(url)
            print(response)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract title
                title = soup.title.string if soup.title else "No title found"

                # Extract description
                description_tag = soup.find("meta", attrs={"name": "description"})
                description = description_tag["content"] if description_tag else "No description found"

                # Extract body text
                body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else "No text found"

                # Extract links
                links = [a.get('href') for a in soup.find_all('a', href=True)]

                result = {
                    "url": url,
                    "title": title,
                    "description": description,
                    "text_body": body_text
                }
                node_types = [
                    'Person', 'Organization', 'Object', 'Concept', 'Event', 
                    'Action', 'Location', 'Time', 'Technology', 'Market', 'Product'
                ]

                edge_types = [
                    'Is a/Type of', 'Related to', 'Part of/Contains', 'Born in/Died in', 
                    'Works for', 'Invented/Discovered', 'Founded in', 'Operates in', 
                    'Produces/Offers', 'Occurs in', 'Involves/Includes', 'Subcategory of', 
                    'Contrasts with', 'Performed by', 'Affects', 'Located in/Found in', 
                    'Originated from', 'Used by/Utilized by', 'Targets/Addresses Market', 
                    'Invests in', 'Collaborates on', 'Worked for', 'Invested in',
                    'Expert in', 'Competes with'
                ]
                # node_types = ['people', 'organizations', 'event','object','concept']
                # edge_types = ['is part of','was part of','is related to','was related to']
                # edge_types = ['invested in','worked at','worked with','works at','investor of','partnered with']
                # node_types = ['diety', 'purana','avatar','concept', 'place','event']
                # edge_types = ['purana_of','avatar_of','parent_child','sibling','friend','lover','fought','also_known_as','associated_with','god_of','worshipped_for']
                #node_types = ['documentation_section', 'concept', 'code_snippet','module','use case','tool']
                #edge_types = ['is part of','relates to','implements','uses','supports']
                result = {
                  'natural_input' : result,
                  'node_types': node_types,
                  'edge_types': edge_types
                }

                # Retrieve the natural_input integration function
                natural_input_function = get_integration_function('natural_input')

                if natural_input_function:
                    # Pass the scraped data to the natural_input integration
                    natural_input_response, status_code = natural_input_function(app, result)
                    if status_code == 200:
                        # Process successful, augment response with natural_input integration's response
                        augmented_result = {
                            **result,
                            "natural_input_response": natural_input_response.get_json()
                        }
                        return jsonify(augmented_result), 200
                    else:
                        return jsonify({"error": "Failed to process data through natural_input integration"}), status_code
                else:
                    return jsonify({"error": "natural_input integration not found"}), 404
            else:
                return jsonify({"error": "Failed to retrieve URL"}), 400
        except Exception as e:
            return jsonify({"error": "Error scraping URL: " + str(e)}), 400

def register(integration_manager):
    integration_manager.register('url_input', url_input)
