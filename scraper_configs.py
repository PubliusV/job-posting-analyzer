from utils.base_utils import get_xpath_text, get_condensed_html, get_untagged_html

SCRAPER_CONFIGS = {
                "template_validation_scraper": { "name":"template_validation_scraper",
                "job_pattern":"\/en\/jobs\/\S",
                "id_pattern":"jobs\/(.+?)\/",
                "domain":"https://careers.example.com",
                "xpaths":[
                    {"name":"title","xpath":"PATH_TO_TITLE","func":get_xpath_text},
                    {"name":"description","xpath":"PATH_TO_BODY","func":get_condensed_html},
                    {"name":"meta","xpath":"PATH_TO_METADATA","func":get_untagged_html}
                ]
                },

                "api_scraper_with_analysis" : { "name":"api_scraper_with_analysis",
                "job_pattern":"/en/job/",
                "id_pattern":"(R\d*?)\/",
                "domain":"https://ocs.example.com",
                "xpaths":[
                    {"name":"title","xpath":"PATH_TO_TITLE","func":get_xpath_text},
                    {"name":"description","xpath":"PATH_TO_BODY","func":get_condensed_html},
                    {"name":"meta","xpath":"PATH_TO_METADATA","func":get_untagged_html}
                    ]
                },

                "undetected_chrome_scraper" : { "name":"undetected_chrome_scraper",
                "job_pattern":"/en/job/",
                "id_pattern":"(R\d*?)\/",
                "domain":"https://careers.example.com/example-jobs",
                "xpaths":[
                    {"name":"title","xpath":"PATH_TO_TITLE","func":get_xpath_text},
                    {"name":"description","xpath":"PATH_TO_BODY","func":get_condensed_html},
                    {"name":"meta","xpath":"PATH_TO_METADATA","func":get_untagged_html}
                    ]
                },

                "session_api_scraper": { "name":"session_api_scraper",
                "job_pattern":"",
                "id_pattern":"",
                "domain":"https://jobs.example.com/careers",
                "xpaths":[
                    {"name":"title","xpath":"PATH_TO_TITLE","func":get_xpath_text},
                    {"name":"description","xpath":"PATH_TO_BODY","func":get_condensed_html},
                    {"name":"meta","xpath":"PATH_TO_METADATA","func":get_untagged_html}
                    ]
                },

                "basic_xpath_scraper" : { "name":"basic_xpath_scraper",
                "job_pattern":"\/en\/jobs\/",
                "id_pattern":"",
                "domain":"https://www.examplejobs.com/sitemap.xml",
                "xpaths":{
                    "title":"PATH_TO_TITLE",
                    "description":"PATH_TO_BODY",
                    "meta":"PATH_TO_METADATA"
                    }
                },

                "custom_xml_scraper": { "name":"custom_xml_scraper",
                "job_pattern":"/jobs/.*lang=en-us",
                "id_pattern":"jobs\/(.+?)[?]",
                "domain":"https://careers.example.com/sitemap1.xml",
                "xpaths":[
                    {"name":"title","xpath":"PATH_TO_TITLE","func":get_xpath_text},
                    {"name":"description","xpath":"PATH_TO_BODY","func":get_condensed_html},
                    {"name":"meta","xpath":"PATH_TO_METADATA","func":get_untagged_html}
                ]
                },

                "greenhouse_api_scraper": { "name":"greenhouse_api_scraper",
                "job_pattern":"/jobs/.*gh_jid",
                "id_pattern":"jobs\/(.+?)[?]",
                "domain":"https://www.example.com/company/careers/opportunities.html",
                "xpaths":[
                    {"name":"title","xpath":'PATH_TO_TITLE',"func":get_xpath_text},
                    {"name":"description","xpath":'PATH_TO_BODY',"func":get_condensed_html},
                    {"name":"meta","xpath":'PATH_TO_METADATA',"func":get_untagged_html}
                ]
                },

            }