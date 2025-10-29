from utils.base_utils import *

"""
NEVER - EVER - commit credentials to GitHub.
Whether you want to use environment variables or store them in a local file,
these are the variable names I used in this script for the necessary credentials
should you want to find/replace on them.

- OPENAI_API_KEY
- LANG_TOOLS_UNAME
- LANG_TOOLS_API_KEY
"""

COMPATIBLE_COMPANIES = ['template_validation',"api_company_with_analysis","undetected_chrome","session_api","basic_xpath_company", "xml_company","greenhouse_company"]

BASE_HEADERS = ['url',
            'title',
            'job_desc',
            'job_info_raw',
            'masculine_word_count',
            'feminine_word_count',
            'grammar_mistakes',
            'spelling_mistakes',
            'langtools_detail',
            'bullet_point_count',
            'count_of_duplicate_sentences',
            'jd_structure_eval',
            'salary_compliance',
            'jd_text_eval',
            "cx_eval_1",
            "cx_eval_2",
            "cx_eval_3",
            "cx_eval_4",
            "cx_eval_5"]
