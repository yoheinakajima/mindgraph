# This code demonstrates integrating OpenAI's GPT-4 model within a Flask application for processing natural language inputs
# to automatically generate a structured knowledge graph. The integration leverages the application's integration manager system
# for enhanced functionality.

# The `create_knowledge_graph` function invokes OpenAI's ChatCompletion API with a specialized prompt that guides the AI to
# process the given natural language input. It aims to construct a knowledge graph identifying entities such as people, organizations,
# and events, along with their interrelationships, based on the input. The function specifies a strict output structure, including
# node types and details about the relationships, to ensure the generated knowledge graph adheres to a predefined format useful for
# application purposes. After receiving the AI's response, the function extracts and returns the structured knowledge graph data.

# The `natural_input` function acts as an integration endpoint within the Flask application. It receives natural language input,
# employs the `create_knowledge_graph` function to generate a knowledge graph from this input, and processes the resulting data.
# Key to this function is the invocation of the `add_multiple_conditional_function`, retrieved through the application's integration
# manager. This function is responsible for adding the generated knowledge graph entities and their relationships into the application's
# data model, based on conditional logic predefined within the integration. This allows for dynamic and automated updates to the
# application's data based on the content of the natural language input processed.

# Error handling is incorporated to ensure a graceful response in case of failures, which could arise from the OpenAI API call,
# data processing errors, or issues in retrieving or executing the `add_multiple_conditional_function`. The system is designed to
# return a structured JSON response indicating the nature of the error encountered.

# Additionally, the `register` function is used to associate the `natural_input` functionality with the application's integration
# manager. This registration facilitates the invocation of the `natural_input` process as a part of the application's broader set
# of integrations, seamlessly integrating AI-driven natural language processing capabilities into the application's ecosystem.

# This integration exemplifies the use of AI to enrich web applications, enabling the transformation of natural language inputs
# into structured data through automated knowledge graph generation and the conditional addition of this data into the application's
# operational context, leveraging the `add_multiple_conditional_function` for dynamic data integration based on AI-generated content.

# This code demonstrates integrating OpenAI's GPT-4 model within a Flask application for processing natural language inputs
# to automatically generate a structured knowledge graph. The integration leverages the application's integration manager system
# for enhanced functionality.

# The `create_knowledge_graph` function invokes OpenAI's ChatCompletion API with a specialized prompt that guides the AI to
# process the given natural language input. It aims to construct a knowledge graph identifying entities such as people, organizations,
# and events, along with their interrelationships, based on the input. The function specifies a strict output structure, including
# node types and details about the relationships, to ensure the generated knowledge graph adheres to a predefined format useful for
# application purposes. After receiving the AI's response, the function extracts and returns the structured knowledge graph data.

# The `natural_input` function acts as an integration endpoint within the Flask application. It receives natural language input,
# employs the `create_knowledge_graph` function to generate a knowledge graph from this input, and processes the resulting data.
# Key to this function is the invocation of the `add_multiple_conditional_function`, retrieved through the application's integration
# manager. This function is responsible for adding the generated knowledge graph entities and their relationships into the application's
# data model, based on conditional logic predefined within the integration. This allows for dynamic and automated updates to the
# application's data based on the content of the natural language input processed.

# Error handling is incorporated to ensure a graceful response in case of failures, which could arise from the OpenAI API call,
# data processing errors, or issues in retrieving or executing the `add_multiple_conditional_function`. The system is designed to
# return a structured JSON response indicating the nature of the error encountered.

# Additionally, the `register` function is used to associate the `natural_input` functionality with the application's integration
# manager. This registration facilitates the invocation of the `natural_input` process as a part of the application's broader set
# of integrations, seamlessly integrating AI-driven natural language processing capabilities into the application's ecosystem.

# This integration exemplifies the use of AI to enrich web applications, enabling the transformation of natural language inputs
# into structured data through automated knowledge graph generation and the conditional addition of this data into the application's
# operational context, leveraging the `add_multiple_conditional_function` for dynamic data integration based on AI-generated content.

from flask import Flask, request, jsonify
import openai
import json
from app.integration_manager import get_integration_function

app = Flask(__name__)


def create_knowledge_graph(app, natural_input):
    with app.app_context():
        try:
            print("start openai call")

            with open("schema.json", "r") as file:
                schema = json.load(file)

            nodes_properties = {}
            node_types = []
            all_edge_types = set()

            for node_type, info in schema.items():
                all_edge_types.update(info["edge_types"].keys())
                node_types.append(info["node_type"])  # Collect node types
                edges = list(info["edge_types"].keys())
                properties = {
                    "temp_id": {"type": "integer"},
                    "name": {"type": "string"},
                }

                # Add additional properties based on the schema
                for edge_type, description in info["edge_types"].items():
                    properties[edge_type] = {
                        "type": "string",
                        "description": description,
                    }

                nodes_properties[node_type] = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": properties,
                        "required": ["temp_id", "name"],
                    },
                }

            edges = list(all_edge_types)
            # print(f"edges: {edges}\n")

        except Exception as e:
            print(f"Error during knowledge graph creation: {e}")
            return jsonify({"error": str(e)}), 500

        completion = openai.ChatCompletion.create(
            model="gpt-4-0125-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                You are an AI expert specializing in knowledge graph creation with the goal of capturing relationships based on a given input or request.
                You are given input in various forms such as paragraph, email, text files, and more.
                Your task is to create a knowledge graph based on the input.
                Only use organizations, people, and events as nodes and do not include concepts or products.
                Only add nodes that have a relationship with at least one other node.
                Make sure that the node type (people, org, event) matches the to_type or for_type when the entity is part of a relationship.
              """,
                },
                {
                    "role": "user",
                    "content": f"Help me understand the following by creating a structured knowledge graph: Person A works at Org B. Person C works at Org B. Org D invested in Org B. Person E works at Org D.",
                },
                {
                    "role": "assistant",
                    "content": '{"nodes":{"Person":[{"temp_id":1,"name":"Person A"},{"temp_id":2,"name":"Person C"},{"temp_id":3,"name":"Person E"}],"Organization":[{"temp_id":4,"name":"Org B"},{"temp_id":5,"name":"Org D"}]},"relationships":[{"from_type":"Person","from_temp_id":1,"to_type":"Organization","to_temp_id":4,"data":{"relationship":"Works at"}},{"from_type":"Person","from_temp_id":2,"to_type":"Organization","to_temp_id":4,"data":{"relationship":"Works at"}},{"from_type":"Organization","from_temp_id":5,"to_type":"Organization","to_temp_id":4,"data":{"relationship":"Invested in"}},{"from_type":"Person","from_temp_id":3,"to_type":"Organization","to_temp_id":5,"data":{"relationship":"Works at"}}]}',
                },
                {
                    "role": "user",
                    "content": f"Help me understand the following by creating a structured knowledge graph: {natural_input}",
                },
            ],
            functions=[
                {
                    "name": "knowledge_graph",
                    "description": f"Generate a knowledge graph with entities and relationships. Node types must be in {node_types}. Do your best to capture relationships. Do not abbreviate anything. Do not provide a response that is not part of the JSON.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nodes": {
                                "type": "object",
                                "properties": nodes_properties,
                            },
                            "relationships": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "from_type": {
                                            "type": "string",
                                        },
                                        "from_temp_id": {"type": "integer"},
                                        "to_type": {
                                            "type": "string",
                                        },
                                        "to_temp_id": {"type": "integer"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "relationship": {
                                                    "type": "string",
                                                    "description": "Detailed relationship information between the two properties.",
                                                    "enum": edges,
                                                },
                                                "snippet": {
                                                    "type": "string",
                                                    "description": "Provide a snippet from the source word for word (either one or more full sentences) describing this relationship between the two entities.",
                                                },
                                            },
                                            "required": ["relationship", "snippet"],
                                        },
                                    },
                                    "required": [
                                        "from_type",
                                        "from_temp_id",
                                        "to_type",
                                        "to_temp_id",
                                        "data",
                                    ],
                                },
                            },
                        },
                        "required": ["nodes", "relationships"],
                    },
                }
            ],
            function_call={"name": "knowledge_graph"},
        )
        print("OPENAI END")
        print(completion.choices[0])

        response_data = completion.choices[0]["message"]["function_call"]["arguments"]

        return response_data


def natural_input(app, data):
    with app.app_context():
        try:
            # Assume create_knowledge_graph returns the correct data structure
            knowledge_graph_data = create_knowledge_graph(app, data)
            knowledge_graph_data = json.loads(knowledge_graph_data)

            # Retrieve the callable function for the add_multiple_conditional integration
            print("get function")
            add_multiple_conditional_function = get_integration_function(
                "add_multiple_conditional"
            )

            if not add_multiple_conditional_function:
                raise ValueError("Target integration function not found")

            # Prepare the data in the format expected by the add_multiple_conditional integration

            print("start adding")
            add_multiple_conditional_data = knowledge_graph_data

            # Call the target integration function and get the response
            response = add_multiple_conditional_function(
                app, add_multiple_conditional_data
            )

            return response
        except Exception as e:
            print(f"Failed to trigger add_multiple_conditional: {e}")
            return jsonify({"error": str(e)}), 500


def register(integration_manager):
    integration_manager.register("natural_input", natural_input)
