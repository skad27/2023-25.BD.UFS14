
import requests
import pytest
from jsonschema import validate
from mymodule import get_pubchem_cid

# Definizione dello schema JSON
pubchem_schema = {
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

def test_pubchem_contract():
    session = requests.Session()
    ingredient_name = "Aspirin"
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/cids/JSON"
    response = session.get(url)
    data = response.json()
    # Validazione dello schema
    validate(instance=data, schema=pubchem_schema)