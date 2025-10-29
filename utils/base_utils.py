# Standard library imports
import json
import logging
import re
from logging.handlers import RotatingFileHandler

# Third-party imports
import htmlmin
import lxml
from bs4 import BeautifulSoup
from lxml import html
from lxml.html.clean import Cleaner
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Local application imports
from constants import OPENAI_API_KEY
from utils.langtools import check_language, process_langtools_response

# Logger configuration
logger = logging.getLogger("JD_Scraper")
logger.setLevel(logging.INFO)

"""
NOTE: This code has been anonymized for portfolio purposes.
Actual implementations, patterns, and business logic have been
modified or redacted to protect client confidentiality.
"""


def log_openai_usage(openai_api_response, prompt_header, company, dev_mode):
    if dev_mode == 0: # if defv mode is on, we aren't using the API, so no logs.
        logger.info(f"[ company : {company} ] - [ prompt_type : {prompt_header} ] - [ prompt_tokens : {openai_api_response.prompt_tokens} ] - [ response_tokens : {openai_api_response.completion_tokens} ] - [ cached_tokens : {openai_api_response.prompt_tokens_details.cached_tokens} ]")

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def run_prompt(sys_prompt:str,user_prompt:str, dev_mode:int=0)->str:
    if dev_mode == 0:
        client = OpenAI(
                api_key=OPENAI_API_KEY
            )
        session = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[ { "role": "system", "content" : sys_prompt },
                            {"role": "user", "content": user_prompt } ]
                    )

        message_response = session.choices[0].message.content
        usage_response = session.usage
        ## print(usage_response)
        return message_response, usage_response
    else:
        return "This row processed in developer mode.", "No Usage"

def count_bullets(html_string:str) -> int:
    return (len(html_string)-len(html_string.replace("<li>","")))//4

def gender_analysis(text:str, gender:str) -> int:

    gendered_words = {
        "masculine":[
            "word_1","word_2","word_3"
        ],
        "feminine":[
            "word_1","word_2","word_3"
        ] 
    } # Actual gender-coded word list redacted

    text = text.lower()
    words = text.split()
    count = 0

    for word in words:
        if word.startswith(tuple(gendered_words[gender])):
            count+=1
    return count

def get_langtools_feedback(job_description_text):
    try:
        langtools_evaluation = process_langtools_response(check_language(job_description_text))
        issue_types = [key for key, value in langtools_evaluation['issues'].items()]

        spelling_mistakes = langtools_evaluation["issues"].get('Spelling mistake', 0)
        non_spelling_issues = [value for key, value in langtools_evaluation['issues'].items() if key not in ['Spelling mistake']]
        grammar_mistakes = sum(non_spelling_issues)

    except Exception as e:
            # Log exception for debugging
            print(f"Exception when calling LangTools API: {e}")
            print("Continuing analysis without LangTools...")
            langtools_evaluation = {"issues":None, "context":None}
            spelling_mistakes = None
            grammar_mistakes = None

    return spelling_mistakes, grammar_mistakes, langtools_evaluation['issues']

def preprocess_description_text(jd_description):
    try:
        html = BeautifulSoup(jd_description["description"],features="lxml")
        for strong_item in html.find_all(["strong","b","i"]):
                strong_item.unwrap()
        for div_item in html.find_all(["div","p"]):
                div_item.smooth()

        html_as_text = html.get_text("\n", strip=True)

        return html_as_text
    except:
        return "unable to parse html"

def get_xpath_text(element):
    return element[0].text

def get_untagged_html(element):
    return untag_html(element[0].get_attribute('innerHTML'))

def get_condensed_html(element):
    return condense_html(element[0].get_attribute('innerHTML'))

def condense_html(raw_html : str) -> str:
    """
    Minify and clean the HTML content, stripping unnecessary comments, whitespace, and elements like JavaScript and style tags.
    """
    if not raw_html:
        return ""

    minified = htmlmin.minify(raw_html,remove_comments=True,reduce_boolean_attributes=True)
    cleaner = Cleaner()
    cleaner.javascript = True 
    cleaner.style = True
    
    return cleaner.clean_html(minified)

def untag_html(html: str) -> str:
    """
    Clean the HTML content by removing all tags, leaving only plain text.
    """

    if not html:
        return ""

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')

    for tag in ['a', 'strong', 'b', 'i']:
        for match in soup.find_all(tag):
            match.unwrap()

    # Get the plain text, removing all tags
    plain_text = soup.get_text(separator='\n', strip=True)

    # Optionally, use regex to remove extra spaces or newline characters
    plain_text = re.sub(r'[^\S\n]+', ' ', plain_text)

    return plain_text

def save_checkpoint(last_scraped_url, latest_scrape_data):
    with open('checkpoint.json', 'w') as f:
        json.dump({"last_scraped": last_scraped_url}, f)
    with open('data_checkpoint.json','w') as f:
        json.dump({"payload": latest_scrape_data}, f)

def load_checkpoint():
    try:
        with open('checkpoint.json', 'r') as f:
            data = json.load(f)
            return data.get("last_scraped", None)
    except FileNotFoundError:
        return None

def load_checkpoint_data():
    try:
        with open('data_checkpoint.json', 'r') as f:
            data = json.load(f)
            return data.get("payload", None)
    except FileNotFoundError:
        return None