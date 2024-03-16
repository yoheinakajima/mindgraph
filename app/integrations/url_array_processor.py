# Used for the csv input, which sends an array of URLs to this function, which splits up and sends to the url_input function which is loaded with the integration manager.

from flask import jsonify
from urllib.parse import urlparse, quote
from app.integration_manager import get_integration_function

# Function to check if a string is a valid URL
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# Updated integration function to process an array of URLs using the Integration Manager
def url_array_processor(app, data):
    with app.app_context():
        print("URL Array Processor Integration")
        urls = data.get('urls', [])  # Expecting 'urls' to be an array of URLs
    
        results = []
        errors = []
    
        # Retrieve the url_input integration function
        url_input_function = get_integration_function('url_input')
    
        if not url_input_function:
            return jsonify({"error": "url_input integration not found"}), 404
    
        for url in urls:
            if is_valid_url(url):
                # Encode the URL
                encoded_url = quote(url, safe='')
                url_input_data = {'natural_input': encoded_url}
    
                # Dynamically call the url_input function
                response, status_code = url_input_function(app, url_input_data)
    
                if status_code == 200:
                    results.append(response)
                else:
                    errors.append(f"Failed to process URL {url}: Status Code {status_code}")
            else:
                errors.append(f"Invalid URL: {url}")
    
        return jsonify({"results": "success", "errors": errors}), 200

# Function to register this integration with the IntegrationManager
def register(integration_manager):
    integration_manager.register('url_array_processor', url_array_processor)
