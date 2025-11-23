import os
import json
import requests
import azure.functions as func

STOP_WORDS = {"the", "is", "at", "which", "on", "and", "a", "an", "of", "for", "to", "in"}

def remove_stop_words(text):
    words = text.split()
    filtered = [w for w in words if w.lower() not in STOP_WORDS]
    return " ".join(filtered)

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

        # Remove stop words
        processed_query = remove_stop_words(user_query)

        # Azure Cognitive Search endpoint for new index
        search_endpoint = f"{os.environ['SEARCH_ENDPOINT']}/indexes/wordprocess/docs/search?api-version=2023-07-01-Preview"
        api_key = os.environ["SEARCH_API_KEY"]

        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
        body = {
            "search": processed_query,
            "select": "FileName,content",
            "top": 5
        }

        # Call Azure Cognitive Search
        response = requests.post(search_endpoint, headers=headers, json=body)
        results = response.json().get("value", [])

        # Format results
        formatted_results = []
        for item in results:
            formatted_results.append({
                "FileName": item.get("FileName", "N/A"),
                "Content": item.get("content", "N/A")
            })

        return func.HttpResponse(
            json.dumps({"status": "success", "results": formatted_results}, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )