# Standard library imports
import datetime
import gc
import logging
from logging.handlers import RotatingFileHandler
import re
import time
import typing

# Third-party imports
import nltk
import openai
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from usp.tree import sitemap_tree_for_homepage

# Local application imports
from constants import *

# Logger configuration
logger = logging.getLogger("JD_Scraper")
logger.setLevel(logging.INFO)

# NLTK setup
nltk.download("punkt_tab")

from utils.base_utils import *

"""
NOTE: This code has been anonymized for portfolio purposes.
Actual implementations, patterns, and business logic have been
modified or redacted to protect client confidentiality.
"""

class ReportConstructor():
    """
    Create default scrape behavior to be modified by overloading in subclasses

    Start by scraping the sitemap. Get a list of url's that we know are JD's.
    Then create a process for processing each JD.
        - open the JD page with a headless browser
        - extract the relevant page elements by XPath
            > Individual XPaths: Title, Description
            > List of misc Xpaths and methods.
                - retrieve text
                - retrieve cleaned html
            > if JD can't be scraped, skip the row and add the url to an "errors" dataset.
        - Once we have the payload, perform the necessary post-processing steps.
            > OpenAI evaluation
            > Regular Expressions
    Write out the payload and the errored url list.
    """
    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0):
        self.TODAYS_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
        self.checkpoint_url = checkpoint_url
        self.caught_up_to_checkpoint = False
        self.headers = BASE_HEADERS
        self.domain = config_args['domain']
        self.xpaths = config_args['xpaths']
        self.sitemap_job_pattern = config_args['job_pattern']
        self.sitemap_id_pattern = config_args['id_pattern']
        self.company_name = config_args['name']
        self.dev_mode = dev_mode

        self._start_browser()
        self.processed_data = []
        self.skipped_urls = []

    def _scrape_sitemap(self):
        tree = sitemap_tree_for_homepage(self.domain)
        data = []

        for page in tree.all_pages():
            print(f"scraping page {page}")
            req_id = None
            # print(page.url)
            # print(f"matching on: {self.sitemap_id_pattern}")
            if match := re.search(self.sitemap_id_pattern, page.url):
                req_id = match.group(1)
            if re.search(self.sitemap_job_pattern, page.url): 
            # and not(req_id in dedupe_on.values):
                data.append([page.url, page.last_modified])
        return data

    def _process_sitemap(self) -> None:
        # surpress warning and info messages coming from USP
        logging.getLogger("usp.fetch_parse").setLevel(logging.CRITICAL)
        logging.getLogger("usp.helpers").setLevel(logging.ERROR)
        logging.getLogger("usp.tree").setLevel(logging.ERROR)

        print(f"| --- Scraping the {self.domain} sitemap for job descriptions --- |")

        output_df = pd.DataFrame(self._get_sitemap_urls(), columns=['url', 'last_modified'])
        output_df['last_modified'] = str(output_df['last_modified'][0])[:10]
        self.manifest_df = output_df
        self.job_counter = 0
        self.num_jobs = len(self.manifest_df['url'])
        print(f"| --- Found {self.num_jobs} Job Descriptions --- |")

    def _process_jd_checkpoint_update(self, url):
        if url == self.checkpoint_url:
            self.caught_up_to_checkpoint = True
            print("Caught up to Checkpoint!")
            print(f"caught up at job number {self.job_counter+1}: {url}")
        # self.job_counter+=1

    def _jd_update_status(self):
        print(f"Successfully scraped [{self.job_counter}/{self.num_jobs}] job descrtiptions.")
        self.browser.delete_all_cookies()
        gc.collect()

    def _process_job_descriptions(self):
        for idx, scrape_row in self.manifest_df.iterrows() :
            try:
                # Check for checkpoint
                if self.checkpoint_url != None and self.caught_up_to_checkpoint == False:
                    self._process_jd_checkpoint_update(scrape_row.url)

                # Print a status update
                if self.job_counter%10 == 0 and self.job_counter!=0:
                    self._update_jd_status()

                # Run basic processing
                raw_job = self._scrape_url(scrape_row.url)
                base_analysis = self._run_base_analysis(raw_job)

                # store the results of the base analysis
                row_data_list = [scrape_row.url,
                    raw_job['title'],
                    raw_job['description'],
                    raw_job['meta'],
                    base_analysis['masculine_count'],
                    base_analysis['feminine_count'],
                    base_analysis['grammar_mistakes'],
                    base_analysis['spelling_mistakes'],
                    base_analysis['langtools_detail'],
                    base_analysis['bullet_point_count'],
                    base_analysis['duplicate_sentences_count'],
                    base_analysis['open_ai_base']["jd_structure_eval"],
                    base_analysis['open_ai_base']["salary_compliance"],
                    base_analysis['open_ai_base']["jd_text_eval"],
                    base_analysis['open_ai_cx']["cx_eval_1"],
                    base_analysis['open_ai_cx']["cx_eval_2"],
                    base_analysis['open_ai_cx']["cx_eval_3"],
                    base_analysis['open_ai_cx']["cx_eval_4"],
                    base_analysis['open_ai_cx']["cx_eval_5"]
                ]
                
                # Process JD with company-specific requirements
                row_data_list.extend(self._extend_with_company_analysis(scrape_row,row_data_list))
                # print(row_data_list)
                # Write all this data to list outside the loop
                self.processed_data.append(row_data_list)
                self.job_counter+=1
                last_scraped_url = scrape_row.url
                save_checkpoint(last_scraped_url, self.processed_data)
            except Exception as e:
                self.skipped_urls.append(scrape_row.url)
                print(f"skipped! Error: {e}")
                continue

    def _start_browser(self): 
        headOption = webdriver.FirefoxOptions()
        headOption.add_argument('-headless')
        self.browser = webdriver.Firefox(options=headOption)

    def _scrape_url(self, url:str) -> dict[str,str]:
        print(f"scraping url: {url}")
        self.browser.get(url)
        time.sleep(5)

        payload = {}
        for path_meta in self.xpaths:
            # print(self.browser.page_source)
            element = self.browser.find_elements(By.XPATH,path_meta['xpath'])
            try:
                payload[path_meta['name']] = path_meta['func'](element)
            except:
                print(f"Oops! We couldn't find the following element: {path_meta['name']} for this job description. Don't worry, we'll get the rest.")
                continue

        assert 'title' in payload, "Config does not contain a title XPath"
        assert 'description' in payload, "Config does not contain a description XPath"
        return payload

    def _run_base_analysis(self, raw_job:dict):
        processed_description = preprocess_description_text(raw_job)
        spelling_mistakes, grammar_mistakes, langtools_detail = get_langtools_feedback(processed_description)

        return {'masculine_count':gender_analysis(raw_job["description"],"masculine"), 
            'feminine_count':gender_analysis(raw_job["description"],"feminine"), 
            'grammar_mistakes':grammar_mistakes,
            'spelling_mistakes':spelling_mistakes,
            'langtools_detail':langtools_detail,
            'bullet_point_count':count_bullets(raw_job['description']),
            'duplicate_sentences_count':self._count_duplicate_sentences(raw_job["description"]), 
            'open_ai_base':self._get_openai_analysis(raw_job["description"]), 
            'open_ai_cx':self._get_openai_analysis(raw_job["description"], mode="cx")}

    def _count_duplicate_sentences(self, corpus:str)->int:
        soup = BeautifulSoup(corpus, "lxml")
        text = soup.get_text()

        sentences = nltk.sent_tokenize(text)
        sent_set = set(sentences)

        diff = len(sentences) - len(sent_set)
        return diff

    def _get_openai_analysis(self, job_description_raw:str, mode:str="base") -> dict[str,str]:
        prompts_lookup = {
            "base":{
                "jd_structure_eval":'PROPRIETARY EVAL QUERY',
                "salary_compliance":'PROPRIETARY EVAL QUERY', 
                "jd_text_eval":'PROPRIETARY EVAL QUERY',
            },
            "cx":{
                "cx_eval_1":'PROPRIETARY EVAL QUERY', 
                "cx_eval_2":"PROPRIETARY EVAL QUERY",
                "cx_eval_3":'''PROPRIETARY EVAL QUERY''',
                "cx_eval_4":'''PROPRIETARY EVAL QUERY''',
                "cx_eval_5":'''PROPRIETARY EVAL QUERY''',
            }
        }
        system_messages = {
            "base":f'Consider this job description: {job_description_raw}',
            "cx":f'''You are a job candidate reviewing a job description for an open role. Consider the following job description: {job_description_raw}'''
        }
        helpers = {
            "base":"OpenAI prompts we run for everyone.",
            "cx":"[C]andidate e[X]perience -- OpenAI prompts geared toward talent attraction."
            }

        assert mode in list(helpers.keys()), f"Mode '{mode}' not available. Options are {helpers}"

        responses = {}

        for header,prompt in prompts_lookup[mode].items():
            try:
                response, usage = run_prompt(system_messages[mode],prompt,dev_mode=self.dev_mode)
                responses[header] = response
                if not self.dev_mode:
                    log_openai_usage(usage, header, self.company_name, self.dev_mode)

            except openai.APIConnectionError as e:
                print("The server could not be reached")
                print(e.__cause__)  # an underlying Exception, likely raised within httpx.
            except openai.RateLimitError as e:
                print("OpenAI says we're yapping; we should back off a bit.")
            except openai.APIStatusError as e:
                print("Another non-200-range status code was received:")
                print(e.status_code)
                print(e.response)

        return responses

    def _run_company_analysis(self,payload):
        ## SHOULD BE OVERLOADED ##
        # Placeholder here to enable functionality
        return []

    def _extend_with_company_analysis(self, source_row, working_payload):
        columns=BASE_HEADERS + [
        "url_sc", "last_modified"
        ]
        payload = working_payload
        payload.extend(source_row)
        return self._run_company_analysis(dict(zip(columns,payload)))

    def _run_company_post_processing(self):
        print(f"Rows: {len(self.processed_data)} x Columns: {len(self.processed_data[0])}")
        self.data_payload = pd.DataFrame(
        self.processed_data,
        columns = BASE_HEADERS
        )

    def process_jobs(self):
        print(f"| --- Processing {self.company_name} sitemap --- |")
        self._process_sitemap()
        print("| --- Processing job descriptions --- |")
        self._process_job_descriptions()
        print("| --- Running post-processing --- |")
        self._run_company_post_processing()

        ## Merge any data originally gotten as part of the base URL scrape with the processed row data.
        self.finalized_dataset = self.manifest_df.merge(self.data_payload,left_index=True,right_index=True, suffixes=(None,"_scraped"))

        self.finalized_dataset['scrape_date'] = self.TODAYS_DATE

        self.finalized_dataset.loc[:,~self.finalized_dataset.columns.str.contains('_sc$|_scraped', regex=True)].to_csv(f"{self.company_name}_merged_table_{self.TODAYS_DATE}.csv",index=False)

        print("File saved! You're all done 👍")
        print(f"Filename: {self.company_name}_merged_table_{self.TODAYS_DATE}.csv")

        if len(self.skipped_urls) > 0:
            skiped_df = pd.DataFrame(self.skipped_urls, columns=['url'])
            skiped_df.to_csv(f"{self.company_name}_skipped_urls_{self.TODAYS_DATE}.csv",index=False)

            print("⚠️ We skipped some url's ⚠️")
            print(f"Filename: {self.company_name}_skipped_urls_{self.TODAYS_DATE}.csv")
