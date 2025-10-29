# Standard library imports
import xml.etree.ElementTree as ET

# Third-party imports
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Local application imports
from constants import *
from utils.report_constructor import *

class CustomXmlScraper(ReportConstructor):
    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0,lookback=None):
        super().__init__(config_args, checkpoint_url, dev_mode)

        assert isinstance(self.xpaths, list), "Xpaths in Company config should be a list of dictionaries with configuration parameters for each XPath."

    def _scrape_sitemap(self):
        sitemap_url = self.domain

        resp = requests.get(sitemap_url)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)

        data = []

        # iterate through all <url> nodes (namespace-agnostic)
        for url_tag in root.findall(".//{*}url"):
            loc = url_tag.find("{*}loc")
            lastmod = url_tag.find("{*}lastmod")

            if loc is None:
                continue

            url = loc.text.strip()
            url = loc.text.strip().replace(".co/", ".com/")
            last_modified = lastmod.text.strip() if lastmod is not None else None

            print(f"scraping page {url}")

            req_id = None
            if match := re.search(self.sitemap_id_pattern, url):
                req_id = match.group(1)

            if re.search(self.sitemap_job_pattern, url):
                data.append([url, last_modified])
        return data

    def _scrape_url(self, url: str) -> dict[str, str]:
        print(f"scraping url: {url}")
        self.browser.get(url)

        payload = {}

        for path_meta in self.xpaths:
            try:
                # Wait up to 10s for the element to be present
                element = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, path_meta['xpath']))
                )
                payload[path_meta['name']] = path_meta['func'](element)
            except Exception as e:
                print(f"Skipped {path_meta['name']}! XPath: {path_meta['xpath']} Error: {e}")
                continue

        # Assertions ensure required fields are captured
        assert 'title' in payload and payload['title'], "Config does not contain a valid title"
        assert 'description' in payload and payload['description'], "Config does not contain a valid description"

        return payload

    def _extend_with_company_analysis(self, source_row, working_payload):
        return []