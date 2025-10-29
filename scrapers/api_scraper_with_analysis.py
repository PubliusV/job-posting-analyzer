# Standard library imports
import json
import re
import typing
from typing import Iterable, Union

# Third-party imports
import pandas as pd
from requests import Session
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Local application imports
from constants import *
from utils.report_constructor import *

class ApiScraperWithAnalysis(ReportConstructor):
    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0, lookback=14):
        ''' Initialize the subclass. Pass relevant arguments to the superclass
        then instantiate the region dictionary
        finally figure out how many jobs we expect to scrape
        '''
        super().__init__(config_args, checkpoint_url, dev_mode)

        self.lookback = lookback

        self.region_lookup = {
            'Country1': 'Region1', 
            'Country2': 'Region1',
        } ## Region mapping redacted for privacy

        # Wait up to 10 seconds for the element to appear

        base_page = self.browser.get("https://ocs.example.com")
        
        jobs_counter = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-filters__counter"))
        )

        # Extract the number
        total_jobs_text = jobs_counter.text  # e.g., "821 Open Jobs"
        total_jobs = int(total_jobs_text.split()[0])
        self.expected_jobs = total_jobs


    def _extend_with_company_analysis(self, source_row, working_payload):
        '''Overload the base function by extending the columns / column names. This sets us up for success when we run the company analysis (the superclass default doesn't include all the metadata we get from API Company's API)'''
        columns=BASE_HEADERS + [
        'id_sc',
        'title_sc',
        'primary_location',
        'posted_date',
        'short_description'
        ]
        payload = working_payload
        payload.extend(source_row)
        return self._run_company_analysis(dict(zip(columns,payload)))

    def _run_company_analysis(self,row):
        '''Perform company-specific processing:
        > lookup API Company's region name using the job's primary location
        > Check if the job metadata includes a Role Type and store it
        > Check if the job metadata includes a job schedule and store it
        > Check for an important element in the section headers
        > Check for bad (copy/paste) description in the JD body
        > Check for API Company's old (bad) format in the JD body
        Return a list of the values'''
        # print(row)
        role_type = ""
        schedule_type = ""
        if row['primary_location'] in self.region_lookup:
            region = self.region_lookup[row['primary_location']]
        else:
            region = "Unassigned"
        role_match = re.search(r"Role Type\n(.*?)\n",row['job_info_raw'])
        if role_match:
            role_type = role_match.group(1)
        schedule_match = re.search(r"Job Schedule\n(.*?)\n",row['job_info_raw'])
        if schedule_match:
            schedule_type = schedule_match.group(1)
        contains_important_element = int(bool(
            re.search("IMPORTANT ELEMENT TEXT",row['section_headers'])
            ))
        contains_bad_desc = int(bool(
            re.search("SEARCH TEXT",row['job_desc'])
            ))
        uses_bad_fmt = int(bool(
            (re.search("FORMAT ELEMENT 1",row['job_desc']) 
            and re.search("FORMAT ELEMENT 2",row['job_desc']) 
            and re.search("FORMAT ELEMENT 3",row['job_desc']) 
            and re.search("FORMAT ELEMENT 4",row['job_desc']) 
            and re.search("FORMAT ELEMENT 5",row['job_desc']))
            ))

        return [region,
                role_type, 
                schedule_type, 
                contains_important_element,
                contains_bad_desc,
                uses_bad_fmt]

    def _run_company_post_processing(self):
        '''Overload function for API Company post-processing
        basically just add the appropriate column names for our
        specialized analysis'''
        self.data_payload = pd.DataFrame(
        self.processed_data,
        columns = BASE_HEADERS + [
            'id_sc',
            'title_sc',
            'primary_location',
            'posted_date',
            'short_description',
            "url_sc",
            "region",
            "role_type",
            "schedule_type",
            "contains_important_element",
            "contains_bad_description",
            "uses_bad_format"
            ]
        )

    def _process_sitemap(self) -> None:
        '''Sitemap processing is client-specific.
        Here we ping API Company's API by spoofing a browser session,
        requesting 50 jobs at a time until we reach the number of jobs we
        expected when we initialized the subclass.'''

        print("[ 1 ] - Scraping API Company for Job urls and other data - [ 1 ]")
        print(f" ! Expecting {self.expected_jobs} Job Descriptions ! ")
        session = Session()
        cookies = {
            'COOKIE':'PAYLOAD'
        }

        headers = {
            'HEADER':'PAYLOAD'
        }

        LIMIT = 50
        LAST_ITEM = LIMIT-1
        offset = 0
        total_jobs = 0
        oldest_date = datetime.datetime.now().date()
        lookback_datetime = datetime.datetime.now() - datetime.timedelta(days = self.lookback)
        lookback_date = lookback_datetime.date()

        columns=['id','title','primary_location','posted_date','short_description',"url"]
        scrape_payload = []

        while self.expected_jobs > total_jobs:
            print(f"Scraping jobs {offset}-{offset+LIMIT}... ")
            response = session.get(
                f'https://ocs.example.com/hcmRestApi/resources/latest/limit={LIMIT},sortBy=POSTING_DATES_DESC,offset={offset}',
                cookies=cookies,
                headers=headers,
            )
            response_parsed = json.loads(response.text)

            for jd in response_parsed['items'][0]['requisitionList']:
                scrape_payload.append([jd['Id'],jd['Title'],jd['PrimaryLocation'],jd['PostedDate'],jd['ShortDescriptionStr'],"https://ocs.example.com/en/sites/job/"+jd['Id']])

            offset+=LIMIT
            total_jobs+=LIMIT

        payload = pd.DataFrame(scrape_payload, columns=columns)
        self.manifest_df = payload
        self.job_counter = 0
        self.num_jobs = len(self.manifest_df['url'])
        print(f"| --- Found {self.num_jobs} Job Descriptions --- |")