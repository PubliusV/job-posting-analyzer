# Third-party imports
import requests
from requests import Session

# Local application imports
from constants import *
from utils.report_constructor import *


class SessionApiScraper(ReportConstructor):
    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0,lookback=14):
        super().__init__(config_args, checkpoint_url, dev_mode)

        assert isinstance(self.xpaths, list), "Xpaths in Siemens config should be a list of dictionaries with configuration parameters for each XPath."

        self.session = Session()
        self.cookies = {
            'COOKIE': 'PAYLOAD',
            }

        self.headers = {
            'HEADER': 'PAYLOAD',
            }
        self.start = 0
        self.LIMIT = 10
        self.LAST_ITEM = self.LIMIT - 1
        self.offset = 1
        self.lookback = lookback
        self.oldest_date = datetime.datetime.now().date()
        self.lookback_datetime = datetime.datetime.now() - datetime.timedelta(days = self.lookback)
        self.lookback_end_dt = datetime.datetime.now() - datetime.timedelta(days = self.start)
        self.lookback_end_date = self.lookback_end_dt.date()
        self.lookback_date = self.lookback_datetime.date()
        self.sitemap_cols = ['id','title','primary_location','posted_date','department','business_unit','work_location_option','is_private',"url"]

    def _process_sitemap(self):
        scrape_payload = []
        print(f"| --- Scraping the {self.domain} site API for job descriptions --- |")
        while self.oldest_date >= self.lookback_date:
            print(f"Scraping jobs {self.offset}-{self.offset+self.LIMIT}... ")

            params = [
                ('domain', 'example.com'),
                ('start', f'{self.offset}'),
                ('num', f'{self.LIMIT}'),
                ('query', 'DEPARTMENT'),
                ('pid', 'SAMPLE'),
                ('sort_by', 't_create'),
            ]

            response = self.session.get(
                'https://jobs.example.com/api/apply/v2/jobs',
                params=params,
                cookies=self.cookies,
                headers=self.headers,
            )
            response_parsed = json.loads(response.text)

            if datetime.datetime.fromtimestamp(response_parsed['positions'][self.LAST_ITEM]['t_create']).date() < self.oldest_date:
                self.oldest_date = datetime.datetime.fromtimestamp(response_parsed['positions'][self.LAST_ITEM]['t_create']).date()

            for jd in response_parsed['positions']:
                if datetime.datetime.fromtimestamp(jd['t_create']).date() >= self.lookback_date and datetime.datetime.fromtimestamp(jd['t_create']).date() < self.lookback_end_date:
                    scrape_payload.append([jd['job_id'],jd['name'],jd['location'],datetime.datetime.fromtimestamp(jd['t_create']).strftime("%Y-%m-%d"),jd['department'],jd['business_unit'], jd['work_location'],jd['isPrivate'],jd['Url']])

            self.offset+=self.LIMIT

        payload = pd.DataFrame(scrape_payload, columns=self.sitemap_cols)
        self.manifest_df = payload
        self.job_counter = 0
        self.num_jobs = len(self.manifest_df['url'])
        print(f"| --- Found {self.num_jobs} Job Descriptions --- |")