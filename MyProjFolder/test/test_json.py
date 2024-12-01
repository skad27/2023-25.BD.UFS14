
import requests
import pytest
from jsonschema import validate
from mymodule import get_cid

# Definizione dello schema JSON
schema_pubchem = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "IdentifierList": {
            "type": "object",
            "properties": {
                "CID": {
                    "type": "array",
                    "items": {
                        "type": "number"
                    }
                }
            },
            "required": ["CID"]
        }
    },
    "required": ["IdentifierList"]
}

def test_pubchem_schema():
    sess = requests.Session()
    compound = "Aspirin"
    api_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound}/cids/JSON"
    resp = sess.get(api_url)
    json_data = resp.json()
    # Validazione dello schema
    validate(instance=json_data, schema=schema_pubchem)
