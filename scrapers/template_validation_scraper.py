from utils.report_constructor import *
from constants import *

class TemplateValidationScraper(ReportConstructor):
    def __init__(self, config_args:dict, checkpoint_url = None, dev_mode=0,lookback=None):
        super().__init__(config_args, checkpoint_url, dev_mode)

        assert isinstance(self.xpaths, list), "Xpaths in Company config should be a list of dictionaries with configuration parameters for each XPath."

    def _run_company_analysis(self, row):
        # Check to ensure no substantive text before a certain element
        # While accounting for two different client formats:
        no_extra_pre_text = int(
            bool(
                re.match("PATTERN_CHECK,",row['section_headers'])) 
            or bool(
                re.match("""PATTERN_CHECK,""",row['job_desc'])
                )
            )

        # Check for correct usage of KEYPHRASE
        correct_tagline = int(bool(re.search("KEYPHRASE",row['job_desc'])))

        # Check for overall correct template outline
        correct_template = int(
            bool(
            re.search("PATTERN_CHECK",row['job_desc']) 
            and re.search("PATTERN_CHECK",row['job_desc']) 
            and re.search("PATTERN_CHECK",row['job_desc'])
            )
        )
        return [no_extra_pre_text, 
                correct_tagline, 
                correct_template]

    def _run_company_post_processing(self):
        self.data_payload = pd.DataFrame(
        self.processed_data,
        columns = BASE_HEADERS + [
            "url_sc",
            "last_modified",
            "no_extra_pre_text", 
            "is_correct_tagline", 
            "is_correct_template"
            ]
        )