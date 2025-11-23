import os
import json
import requests
import re
import azure.functions as func

STOP_WORDS = {"the", "is", "at", "which", "on", "and", "a", "an", "of", "for", "to", "in"}

def remove_stop_words(text):
    words = text.split()
    filtered = [w for w in words if w.lower() not in STOP_WORDS]
    return " ".join(filtered)

def highlight_matches(text, query):
    for word in query.split():
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub(f"**{word}**", text)
    return text

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        user_query = req_body.get("text")

        if not user_query:
            return func.HttpResponse(
                json.dumps({"error": "Missing 'text' in request body"}),
                status_code=400,
                mimetype="application/json"
            )

        processed_query = remove_stop_words(user_query)

        search_endpoint = f"{os.environ['SEARCH_ENDPOINT']}/indexes/index1/docs/search?api-version=2023-07-01-Preview"
        api_key = os.environ["SEARCH_API_KEY"]

        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
        body = {
            "search": processed_query,
            "top": 5
        }

        response = requests.post(search_endpoint, headers=headers, json=body)
        results = response.json().get("value", [])

        formatted_results = []
        for item in results:
            formatted_results.append({
                "incident": item.get("Incidentid", "N/A"),
                "description": highlight_matches(item.get("Description", "N/A"), processed_query),
                "root_cause": highlight_matches(item.get("RootCause", "N/A"), processed_query),
                "resolution": highlight_matches(item.get("Resolution", "N/A"), processed_query)
            })

        return func.HttpResponse(
            json.dumps({"status": "success", "results": formatted_results}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )