import azure.functions as func
import logging
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import io
import re
import json

app = func.FunctionApp()

def extract_text_from_pdf(url):
    try:
        response = requests.get(url)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            pdf_data = io.BytesIO(response.content)
            reader = PdfReader(pdf_data)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            return text
        else:
            logging.info("PDF not accessible, error")
            return None
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None

def simple_sent_tokenize(text):
    # Split text into sentences based on periods, question marks, exclamation marks
    sentence_endings = re.compile(r'[.!?]')
    sentences = sentence_endings.split(text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def search_terms_in_pdf(url, term):
    text = extract_text_from_pdf(url)
    results = []
    if text:
        if term == 'NOAEL':
            matches = list(re.finditer(r'(\.|\s)(NOAEL[^\.]+)\.', text, re.IGNORECASE))
        elif term == 'LD50':
            matches = list(re.finditer(r'(\.|\s)(LD\s*50[^\.]+)\.', text, re.IGNORECASE))
        else:
            matches = []
        for match in matches:
            phrase = match.group(2)
            sentences = simple_sent_tokenize(phrase)
            for sentence in sentences:
                if len(sentence.split()) <= 50:
                    results.append(sentence.strip())
    return results

def PDF(url):
    logging.info("URL (first page link): %s", url)
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_links = soup.find_all('a')

        if len(pdf_links) > 2:
            pdf_links = pdf_links[2:-1]
        else:
            logging.info("Not enough PDF links found.")
            return []

        pdf_urls = []
        for link in pdf_links:
            provvisorio = link.get('href')
            if provvisorio and not provvisorio.startswith('javascript:'):
                url_completo = 'https://cir-reports.cir-safety.org/' + provvisorio.lstrip('/')
                pdf_response = requests.get(url_completo)
                if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                    pdf_urls.append(url_completo)
                else:
                    logging.info("PDF not accessible, error")
        return pdf_urls
    else:
        logging.info("Unable to retrieve the URL. Status code: %s", response.status_code)
        return []

def farmaci(farmaco):
    farmaco = farmaco.strip().lower()
    try:
        url = "https://www.cir-safety.org/ingredients"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            siti = soup.find_all('a')

            # Create a dictionary mapping ingredient names to their URLs
            drug_to_url = {}
            for link in siti:
                href = link.get('href')
                text = link.text.strip().lower()
                if href and text:
                    drug_to_url[text] = 'https://cir-reports.cir-safety.org' + href

            if farmaco in drug_to_url:
                farmaco_url = drug_to_url[farmaco]
                pdf_urls = PDF(farmaco_url)
                return {'farmaco_url': farmaco_url, 'pdf_urls': pdf_urls, 'farmaco_trovato': True}
            else:
                logging.info("Ingredient not found or name is incomplete.")
                return {'farmaco_trovato': False}
        else:
            logging.info("Unable to retrieve the ingredients URL. Status code: %s", response.status_code)
            return {'farmaco_trovato': False}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return {'farmaco_trovato': False}

def get_all_ingredients():
    try:
        url = "https://www.cir-safety.org/ingredients"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a')

            ingredients = [link.text.strip() for link in links if link.text.strip() and 'cir' not in link.text.lower() and not re.match(r'^[A-Z#!]$', link.text.strip())]

            return ingredients
        else:
            logging.info("Unable to retrieve the ingredients URL. Status code: %s", response.status_code)
            return []
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return []

@app.route(route="MyHttpTrigger", auth_level=func.AuthLevel.ANONYMOUS)
def MyHttpTrigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Get parameters from the request
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)
   
    ingredient_name = req_body.get('ingredient_name')
    action = req_body.get('action')

    if not action:
        return func.HttpResponse("Please provide 'action' in the request body", status_code=400)
   
    if action == 'get_all_ingredients':
        ingredients = get_all_ingredients()
        return func.HttpResponse(json.dumps({'ingredients': ingredients}), status_code=200, mimetype='application/json')

    if not ingredient_name:
        return func.HttpResponse("Please provide 'ingredient_name' in the request body", status_code=400)

    # Process the request
    if action == 'get_pdfs':
        result = farmaci(ingredient_name.lower())
        if result['farmaco_trovato']:
            pdf_urls = result.get('pdf_urls', [])
            return func.HttpResponse(json.dumps({'pdf_urls': pdf_urls}), status_code=200, mimetype='application/json')
        else:
            return func.HttpResponse("Ingredient not found", status_code=404)
    elif action == 'search_noael':
        result = farmaci(ingredient_name.lower())
        if result['farmaco_trovato']:
            pdf_urls = result.get('pdf_urls', [])
            all_noael_results = []
            for pdf_url in pdf_urls:
                results = search_terms_in_pdf(pdf_url, 'NOAEL')
                all_noael_results.extend(results)
            return func.HttpResponse(json.dumps({'NOAEL_results': all_noael_results}), status_code=200, mimetype='application/json')
        else:
            return func.HttpResponse("Ingredient not found", status_code=404)
    elif action == 'search_ld50':
        result = farmaci(ingredient_name.lower())
        if result['farmaco_trovato']:
            pdf_urls = result.get('pdf_urls', [])
            all_ld50_results = []
            for pdf_url in pdf_urls:
                results = search_terms_in_pdf(pdf_url, 'LD50')
                all_ld50_results.extend(results)
            return func.HttpResponse(json.dumps({'LD50_results': all_ld50_results}), status_code=200, mimetype='application/json')
        else:
            return func.HttpResponse("Ingredient not found", status_code=404)
    else:
        return func.HttpResponse("Invalid action", status_code=400)
