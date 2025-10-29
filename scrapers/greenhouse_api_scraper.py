# Standard library imports
import json
import re
import typing
from typing import Iterable, Union

# Third-party imports
import pandas as pd
import requests
from requests import Session

# Local application imports
from constants import *
from utils.report_constructor import *


class GreenhouseApiScraper(ReportConstructor):
    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0, lookback=14):
        super().__init__(config_args, checkpoint_url, dev_mode)

    def _process_sitemap(self) -> None:
        BASE = "https://boards-api.greenhouse.io/v1/boards/example"
        HEADERS = {
            "HEADER":"PAYLOAD"
        }

        resp = requests.get(f"{BASE}/jobs", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        jobs = data.get("jobs", [])   # list of job dicts

        results = []

        for job in jobs:
            url = job.get("absolute_url")
            location = job.get("location", {}).get("name")
            requisition_id = job.get("requisition_id")
            title = job.get("title")
            published = job.get("first_published")

            results.append({
                "url": url,
                "location": location,
                "requisition_id": requisition_id,
                "title": title,
                "published": published,
            })
        
        payload = pd.DataFrame(results)
        self.manifest_df = payload
        self.job_counter = 0
        self.num_jobs = len(self.manifest_df['url'])
        print(f"| --- Found {self.num_jobs} Job Descriptions --- |")
    
    def _extend_with_company_analysis(self, source_row, working_payload):
        return []