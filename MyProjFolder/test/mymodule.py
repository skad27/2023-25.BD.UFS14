import requests
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_cid(session, name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
    try:
        res = session.get(url)
        res.raise_for_status()
        data = res.json()
        cid = str(data['IdentifierList']['CID'][0])
        return cid
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Errore durante il recupero del CID per {name}: {e}")
        return None

def get_ld50(session, cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
    try:
        res = session.get(url)
        res.raise_for_status()
        data = res.json()
        sections = data['Record']['Section']
        ld50_list = []

        def extract_ld50(sec):
            for s in sec:
                if 'Section' in s:
                    extract_ld50(s['Section'])
                if 'Information' in s:
                    for info in s['Information']:
                        if 'Value' in info and 'StringWithMarkup' in info['Value']:
                            for item in info['Value']['StringWithMarkup']:
                                if 'LD50' in item['String']:
                                    ld50_list.append(item['String'])

        extract_ld50(sections)
        return ld50_list if ld50_list else None
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Errore durante il recupero dell'LD50 per CID {cid}: {e}")
        return None
