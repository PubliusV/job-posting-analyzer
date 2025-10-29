from utils.report_constructor import *
from constants import *

class BasicXpathScraper(ReportConstructor):
    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0):
        super().__init__(config_args, checkpoint_url, dev_mode)

        assert isinstance(self.xpaths, list), "Xpaths in Basic XPath Company config should be a list of dictionaries with configuration parameters for each XPath."