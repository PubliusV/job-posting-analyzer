from utils.base_utils import *
from utils.report_constructor import *

from scrapers.template_validation_scraper import *
from scrapers.api_scraper_with_analysis import *
from scrapers.undetected_chrome_scraper import *
from scrapers.session_api_scraper import *
from scrapers.basic_xpath_scraper import *
from scrapers.custom_xml_scraper import *
from scrapers.greenhouse_api_scraper import *

from constants import *
from scraper_configs import *

# Import basics #
import pandas as pd
import argparse
import logging
from logging.handlers import RotatingFileHandler
import sys
import traceback

"""
NOTE: This code has been anonymized for portfolio purposes.
Actual implementations, patterns, and business logic have been
modified or redacted to protect client confidentiality.
"""

# Map scraper type names to their classes
SCRAPER_CLASSES = {
    "template_validation_scraper":TemplateValidationScraper,
    "api_scraper_with_analysis":ApiScraperWithAnalysis,
    "undetected_chrome_scraper":UndetectedChromeScraper,
    "session_api_scraper":SessionApiScraper,
    "basic_xpath_scraper":BasicXpathScraper,
    "custom_xml_scraper":CustomXmlScraper,
    "greenhouse_api_scraper":GreenhouseApiScraper,
}

# parse command line arguments
parser = argparse.ArgumentParser(
    prog='job-scraper',
    description='Scrape and analyze job descriptions from career sites',
    epilog='Example: python main.py -s BasicXPath'
)

parser.add_argument(
    '-s', '--scraper-type', 
    type=str, 
    required=True,
    choices=list(SCRAPER_CLASSES.keys()),
    help='Type of scraper to use'
)

parser.add_argument(
    '-d', '--dev-mode', 
    type=int, 
    default=0, 
    choices=[0,1], 
    help="Dev mode: Skip expensive operations like OpenAI API calls (0=off, 1=on)"
)

parser.add_argument(
    '-l', '--lookback', 
    type=int, 
    default=14, 
    help="Number of days to look back for job postings (for applicable scrapers)"
)

parser.add_argument(
    '--checkpoint', 
    type=int, 
    default=0, 
    choices=[0,1], 
    help="Resume from last checkpoint (0=no, 1=yes)"
)

args = parser.parse_args()

# Set up logging
logger = logging.getLogger('JD_Scraper')
logger.setLevel(logging.INFO)

# Handle checkpoint recovery
checkpoint_url = None
url_scrape_data = None

if args.checkpoint == 1:
    checkpoint_url = load_checkpoint()
    url_scrape_data = load_checkpoint_data()

# Get the appropriate scraper class and configuration
ScraperClass = SCRAPER_CLASSES[args.scraper_type]
config = SCRAPER_CONFIGS[args.scraper_type]

# Initialize the scraper
print(f"\n{'='*60}")
print(f"Initializing {args.scraper_type} scraper")
print(f"Dev mode: {'ON' if args.dev_mode else 'OFF'}")
print(f"{'='*60}\n")

report = ScraperClass(
    config_args=config,
    checkpoint_url=checkpoint_url,
    dev_mode=args.dev_mode,
    lookback=args.lookback
)

# Run the scraping job
try:
    report.process_jobs()
    print("\n✅ Scraping completed successfully!")
except Exception as e:
    print(f"\n❌ Error during scraping: {e}")
    traceback.print_exc()
    sys.exit(1)