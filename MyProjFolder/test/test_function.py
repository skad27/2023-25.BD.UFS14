import pytest
import requests
from mymodule import get_cid

def test_cid_retrieval():
    sess = requests.Session()
    compound = "Aspirina"
    result_cid = get_cid(sess, compound)
    assert result_cid == "2244", "Il CID per l'Aspirina dovrebbe essere '2244'"
