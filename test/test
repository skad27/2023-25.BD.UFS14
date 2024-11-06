import requests
import pytest
import json
from mymodule import get_ld50_pubchem

def test_pubchem_snapshot(snapshot):
    session = requests.Session()
    cid = "2244"  # CID per l'Aspirina
    ld50_values = get_ld50_pubchem(session, cid)
    serialized_data = json.dumps(ld50_values, indent=4)
    snapshot.assert_match(serialized_data, 'pubchem_ld50_snapshot')