import azure.functions as func
import json
import logging
import requests
import urllib.parse

app = func.FunctionApp()

# Function to get the CID of an ingredient from PubChem
def get_pubchem_cid(session, ingredient_name):
    encoded_name = urllib.parse.quote(ingredient_name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/cids/JSON"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        cid = str(data['IdentifierList']['CID'][0])
        return cid
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Error retrieving PubChem CID for {ingredient_name}: {e}")
        return None

# Function to get LD50 values from PubChem
def get_ld50_pubchem(session, cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        sections = data['Record']['Section']
        ld50_values = []
        def extract_ld50(sections):
            for section in sections:
                if 'Section' in section:
                    extract_ld50(section['Section'])
                if 'Information' in section:
                    for info in section['Information']:
                        if 'Value' in info and 'StringWithMarkup' in info['Value']:
                            for item in info['Value']['StringWithMarkup']:
                                if 'LD50' in item['String']:
                                    ld50_values.append(item['String'])
        extract_ld50(sections)
        return ld50_values if ld50_values else None
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Error retrieving LD50 from PubChem for CID {cid}: {e}")
        return None

# Helper function to process the LD50 retrieval
def process_ld50(ingredient_name):
    with requests.Session() as session:
        # Get the CID for the ingredient
        cid = get_pubchem_cid(session, ingredient_name)
        if cid:
            # Get the LD50 values using the CID
            ld50_values = get_ld50_pubchem(session, cid)
            # Return the data as a JSON response
            return func.HttpResponse(
                json.dumps({
                    'ingredient': ingredient_name,
                    'ld50_values': ld50_values or []
                }),
                mimetype="application/json",
                status_code=200
            )
        else:
            return func.HttpResponse(
                f"CID not found for '{ingredient_name}'.",
                status_code=404
            )

# Existing function remains unchanged
@app.route(route="get_ld50", auth_level=func.AuthLevel.ANONYMOUS)
def get_ld50(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing HTTP request for LD50 values of an ingredient.')

    ingredient_name = req.params.get('ingredient_name')

    if not ingredient_name:
        return func.HttpResponse(
            "Please pass an ingredient_name in the query string.",
            status_code=400
        )

    return process_ld50(ingredient_name)

# New function to handle any ingredient name from the URL path
@app.route(route="{ingredient_name}", auth_level=func.AuthLevel.ANONYMOUS)
def get_ld50_by_route(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing HTTP request from URL path for LD50 values of an ingredient.')

    encoded_ingredient_name = req.route_params.get('ingredient_name')

    if not encoded_ingredient_name:
        return func.HttpResponse(
            "Please provide an ingredient name in the URL path.",
            status_code=400
        )

    # Decode the URL-encoded ingredient name
    ingredient_name = urllib.parse.unquote(encoded_ingredient_name)

    return process_ld50(ingredient_name)
