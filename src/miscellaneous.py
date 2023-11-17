import json

def prettify_json(input_json):
    try:
        with open(input_json, 'r') as file:
            json_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        try:
            json_data = json.loads(input_json)
        except json.JSONDecodeError:
            return "Invalid JSON input"

    # Prettify the JSON data
    pretty_json = json.dumps(json_data, indent=4)
    return pretty_json