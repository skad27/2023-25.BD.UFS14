import requests
import pytest
import json
from mymodule import get_ld50

def test_pubchem_ld50(snapshot):
    # Creazione della sessione di rete
    session = requests.Session()

    # Utilizzo di un altro CID, ad esempio "1983" (caffeina)
    cid = "2244"

    # Recupero dei valori LD50
    ld50_data = get_ld50(session, cid)

    # Serializzazione in JSON per confronto
    serialized_ld50 = json.dumps(ld50_data, indent=4)

    # Confronto con lo snapshot fornito
    snapshot.assert_match(serialized_ld50, 'pubchem_ld50_snapshot')
