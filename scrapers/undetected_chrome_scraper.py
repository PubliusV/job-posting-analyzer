# Standard library imports
import json
import re
import typing
from typing import Iterable, Union

# Third-party imports
import pandas as pd
import requests
from requests import Session
import undetected_chromedriver as uc

# Local application imports
from constants import *
from utils.report_constructor import *


class UndetectedChromeScraper(ReportConstructor):

    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0, lookback=14):
        super().__init__(config_args, checkpoint_url, dev_mode)

        self.lookback = lookback

    def _process_sitemap(self) -> None: 
        # surpress warning and info messages coming from USP
        logging.getLogger("usp.fetch_parse").setLevel(logging.CRITICAL)
        logging.getLogger("usp.helpers").setLevel(logging.ERROR)
        logging.getLogger("usp.tree").setLevel(logging.ERROR)

        print(f"| --- Scraping the {self.domain} sitemap for job descriptions --- |")

        output_df = pd.DataFrame(self._get_sitemap_urls(), columns=['url', 'last_modified'])
        output_df['last_modified'] = str(output_df['last_modified'][0])[:10]
        output_df = output_df.head(5)
        self.manifest_df = output_df
        self.job_counter = 0
        self.num_jobs = len(self.manifest_df['url'])
        print(f"| --- Found {self.num_jobs} Job Descriptions --- |")

    def _start_browser(self): 
        options = uc.ChromeOptions()
        self.browser =  uc.Chrome()
    
    def _process_job_descriptions(self):
        for idx, scrape_row in self.manifest_df.iterrows() :
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
                base_analysis['open_ai_cx']["cx_eval_3"],                    base_analysis['open_ai_cx']["cx_eval_4"],
                base_analysis['open_ai_cx']["cx_eval_5"]
            ]

            # Write all this data to list outside the loop
            self.processed_data.append(row_data_list)
            self.job_counter+=1
            last_scraped_url = scrape_row.url
            save_checkpoint(last_scraped_url, self.processed_data)

    def _scrape_url(self, url:str) -> dict[str,str]:
        print(f"scraping url: {url}")
        self.browser.get(url)
        time.sleep(30)

        payload = {}
        for path_meta in self.xpaths:
            element = self.browser.find_elements(By.XPATH,path_meta['xpath'])
            try: 
                payload[path_meta['name']] = path_meta['func'](element)
            except Exception as e:
                payload[path_meta['name']] = e.message if hasattr(e, 'message') else e


        assert 'title' in payload, "Config does not contain a title XPath"
        assert 'description' in payload, "Config does not contain a description XPath"
        return payload