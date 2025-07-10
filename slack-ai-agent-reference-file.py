from flask import Flask, request, jsonify
import requests
import os
import json
import threading
from dotenv import load_dotenv

from tools import get_5xx_error_rate_over_last_1hr, get_latency_report_for_preorder_service

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Path to the reference file
REFERENCE_FILE_PATH = os.environ.get("REFERENCE_FILE_PATH", "knowledge_base.txt")


def load_reference_file():
    """Load the reference file content"""
    try:
        with open(REFERENCE_FILE_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error loading reference file: {e}")
        return "Error: Could not load reference file."


# Load the reference content once at startup
REFERENCE_CONTENT = load_reference_file()


def get_ai_response(user_query):
    """Function to interact with an AI service with the reference content"""
    try:
        # Construct prompt with reference content
        prompt = f"""
Please answer the following query by referring ONLY to the information provided in the REFERENCE CONTENT below and using available tools when needed.
If the answer cannot be found in the reference content, please say that you don't have that information
in your reference materials. Also restrict the output to maximum 150 output_tokens.

USER QUERY: {"can you please explain what this alert means? {}. Also tell me what could be done next to resolve this.".format(user_query)}

REFERENCE CONTENT:
{REFERENCE_CONTENT}
"""
        # Define the tools configuration
        tools_config = [
            {
                "name": "get_latency_report_for_preorder_service",
                "description": "It retrieves the dependent services latency over last 12 hrs from kusto gateway service. Use this when there is a high rate of 4xx HTTP errors for preorder-service.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the backend service for which to construct the latency report",
                        }
                    },
                    "required": ["service_name"],
                },
            },
            {
                "name": "get_5xx_error_rate_over_last_1hr",
                "description": "It retrieves the 5XX error rate over last 1hr when 5xx errors exceed `20%` of requests for 5 minutes, excluding UnknownResource, the alert generally of the form APIErrors5xxHighErrorRate",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the backend service for which to construct the latency report",
                        },
                        "resource_name": {
                            "type": "string",
                            "description": "Name of the resource for which we want to check the 5xx rate. Generally you will get the resource name in a field named like `resource` ",
                        }
                    },
                    "required": ["service_name", "resource_name"],
                },
            }
        ]

        # Make the API call to Anthropic
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20240620",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
                "tools": tools_config,
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": os.environ.get("ANTHROPIC_API_KEY"),
                "anthropic-version": "2023-06-01",
            },
        )

        # Parse the JSON response
        response_data = response.json()
        print(f"\nInitial Response:")
        print(f"Content: {response_data}")

        # Check for tool calls in the response
        while response_data.get("stop_reason") == "tool_use":
            content_list = response_data.get("content", [])
            tool_calls = [
                item for item in content_list if item.get("type") == "tool_use"
            ]
            for tool_call in tool_calls:
                # {'type': 'tool_use', 'id': 'toolu_01UCFHThV4QRr3mBytx5uHZj', 'name': 'get_latency_report_for_preorder_service', 'input': {'service_name': 'preorder-service'}}
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("input")
                if isinstance(tool_input, str):
                    tool_input = json.loads(tool_input)

                print(f"\nTool Used: {tool_name}")
                print(f"Tool Input:")
                print(json.dumps(tool_input, indent=2))

                # Call the tool function
                if tool_name == "get_latency_report_for_preorder_service":
                    tool_result = get_latency_report_for_preorder_service(
                        tool_input.get("service_name")
                    )
                elif tool_name == "get_5xx_error_rate_over_last_1hr":
                    tool_result = get_5xx_error_rate_over_last_1hr(
                        tool_input.get("service_name"),
                        tool_input.get("resource_name")
                    )    
                else:
                    tool_result = {"error": "Unknown tool"}

                print(f"\nTool Result:")
                print(json.dumps(tool_result, indent=2))

                # Make follow-up API call with tool results
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    json={
                        "model": "claude-3-5-sonnet-20240620",
                        "max_tokens": 1000,
                        "messages": [
                            {"role": "user", "content": prompt},
                            {
                                "role": "assistant",
                                "content": response_data.get("content", [{}])[0].get(
                                    "text", ""
                                ),
                            },
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Tool response:"},
                                    {"type": "text", "text": json.dumps(tool_result)},
                                ],
                            },
                        ],
                    },
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": os.environ.get("ANTHROPIC_API_KEY"),
                        "anthropic-version": "2023-06-01",
                    },
                )
                response_data = response.json()

        # Get the final response text from the content array
        final_response = response_data.get("content", [{}])[0].get("text", "")
        print("final_response")
        print(response_data)
        return final_response

    except Exception as e:
        print(f"Error calling AI service: {e}")
        return "Sorry, I encountered an error processing your request."


def process_slash_command(data):
    """Process the slash command asynchronously"""
    print(data)
    try:
        user_query = data.get("text", "").strip()
        channel = data.get("channel")
        thread_ts = data.get("thread_ts")
        response_url = data.get("response_url")

        if not user_query:
            # If no query is provided
            response_message = (
                "Please provide a question or request after the slash command."
            )
        else:
            # Get AI response using the reference file
            ai_response = get_ai_response(user_query)
            response_message = f"{ai_response}"

        print(response_message)    

        # Send the response back to Slack
        requests.post(
            response_url,
            json={"text": response_message, "channel": channel, "thread_ts": thread_ts},
        )
    except Exception as e:
        print(f"Error processing slash command: {e}")

        # Send error message back to Slack
        requests.post(
            response_url,
            json={
                "response_type": "ephemeral",
                "text": "Sorry, something went wrong processing your request.",
            },
        )


@app.route("/slack/ai-assistant", methods=["POST"])
def slack_ai_assistant():
    """Route that handles the Slack slash command"""

    # Get the slash command data
    data = request.get_json()

    # Acknowledge receipt immediately
    response = {
        "response_type": "ephemeral",
        "text": "Processing your request...",
    }

    # Process the command asynchronously
    threading.Thread(target=process_slash_command, args=(data,)).start()

    return jsonify(response)


# Endpoint to refresh the reference file content
@app.route("/admin/refresh-reference", methods=["POST"])
def refresh_reference():
    """Admin endpoint to refresh the reference content"""
    # In a production app, you would add authentication here
    global REFERENCE_CONTENT
    REFERENCE_CONTENT = load_reference_file()
    return jsonify({"status": "success", "message": "Reference content refreshed"})


@app.route("/slack/events", methods=["POST"])
def slack_events():
    # Get the JSON data from the request
    data = request.json

    # Check if this is a challenge request
    if data and "challenge" in data:
        # Log the challenge for debugging
        print(f"Received Slack challenge: {data['challenge']}")

        # Return the challenge value to complete the verification
        return jsonify({"challenge": data["challenge"]})

    # If it's not a challenge, process other types of events
    elif data and "event" in data:
        # Log the event type
        event_type = data["event"].get("type", "unknown")
        message_text = data["event"].get("text")
        print(f"Received Slack event: {message_text}")

        payload = {
            "channel": data["event"].get("channel"),
            "thread_ts": data["event"].get("event_ts"),
            "user_name": data["event"].get("user"),
            "text": "can you please explain what this alert means? {}".format(
                message_text
            ),
            "response_url": "https://hooks.slack.com/services/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",
        }

        # Process the command asynchronously
        threading.Thread(target=process_slash_command, args=(payload,)).start()

        # Return a 200 OK response to acknowledge receipt
        return jsonify({"status": "ok"}), 200

    # For any other type of request
    return jsonify({"status": "error", "message": "Invalid request"}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
