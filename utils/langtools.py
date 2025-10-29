# Standard library imports
import json
import typing

# Third-party imports
import pandas as pd
import requests

# Local application imports
from constants import LANG_TOOLS_API_KEY, LANG_TOOLS_UNAME

"""
NOTE: This code has been anonymized for portfolio purposes.
Actual implementations, patterns, and business logic have been
modified or redacted to protect client confidentiality.
"""

def check_language(corpus:str):
   
    payload = {
        "text":corpus,
        "language":"auto",
        "username":LANG_TOOLS_UNAME,
        "apiKey":LANG_TOOLS_API_KEY,
        "disabledRules":"WHITESPACE_RULE, SENTENCE_WHITESPACE, SPACE_BEFORE_FINAL_PUNCTUATION_MARK, CONSECUTIVE_SPACES, CURRENCY_SPACE, COMMA_PARENTHESIS_WHITESPACE, APOS_SPACE_CONTRACTION"
    }
    response = requests.post("https://api.languagetoolplus.com/v2/check", data=payload)
    response.raise_for_status()
    return response

def process_langtools_response(response_obj) -> list[ str,list[str,str] ]:
    payload = json.loads(response_obj.text)
    issues = {} # [TYPE (shortMessage), CONTEXT OBJ (context:dict)]
    issue_context = []

    if payload["matches"]:
        for match in payload['matches']:
            if match["shortMessage"] in ["Official spelling", "Spelling mistake"] or match["rule"]["category"]["name"] == "Possible Typo":
                issue_name = "Spelling mistake"
                issue_context.append(["ISSUE TYPE: "+issue_name,"RULE DESCRIPTION: "+match["rule"]["description"],"IMMEDIATE CONTEXT: "+match["context"]["text"],"FULL SENTENCE: "+match["sentence"]])
            else:
                issue_name = match["rule"]["category"]["name"]
                issue_context.append(["ISSUE TYPE: "+issue_name,"RULE DESCRIPTION: "+match["rule"]["description"],"IMMEDIATE CONTEXT: "+match["context"]["text"],"FULL SENTENCE: "+match["sentence"]])
            try:
                issues[issue_name]+=1
            except KeyError:
                issues[issue_name]=1
    else:
        issue_context.append("No Issues Returned")

    spelling_mistakes = 0
    if issues.get('Spelling mistake'):
        spelling_mistakes = issues['Spelling mistake']
        
    non_spelling_issues = [value for key, value in issues.items() if key not in ['Spelling mistake']]

    grammar_mistakes = sum(non_spelling_issues)

    return {'language' : payload['language']['name'], 'issues':issues, }