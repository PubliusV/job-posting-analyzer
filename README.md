# Job Description Scraper Framework

A flexible, extensible framework for scraping and analyzing job postings from various career sites. This project supports multiple scraper patterns to handle different site architectures, authentication requirements, and anti-bot measures.

## 🚧 Functionality

This code is redacted/anonymized and business logic has been altere/simplified in order to preserve confidentiality. While the code should remain functional, the anonymization process meant replacing working links with samples (i.e. jobs.example.com) and recoding some variable names, so don't expect to be able to download this code and simply run it without issue. Its purpose here is to showcase how I write code and data processing pipelines.

## 🎯 Features

- **Multiple Scraper Patterns**: 7 different scraper types for various use cases
- **Natural Language Analysis**: Integrates with OpenAI for content analysis
- **Grammar & Spelling Checks**: Uses LanguageTool API for quality assessment
- **Gender-Coded Language Detection**: Identifies masculine/feminine-coded words
- **Template Validation**: Ensures job postings follow organizational standards
- **Checkpoint System**: Resume interrupted scrapes from last saved position
- **Configurable**: Easy-to-modify YAML-like configuration for each site

## 📁 Project Structure

```
job-scraper/
├── main.py                          # Entry point
├── constants.py                     # Configuration constants
├── scraper_configs.py               # Site-specific configurations
├── utils/
│   ├── report_constructor.py            # Base scraper class
│   ├── base_utils.py                    # Utility functions
│   ├── langtools.py                     # LanguageTool integration
├── scrapers/
│   ├── basic_xpath_scraper.py       # Simple sitemap + XPath
│   ├── api_scraper_with_analysis.py # API with business logic
│   ├── greenhouse_api_scraper.py    # Greenhouse ATS integration
│   ├── session_api_scraper.py       # Authenticated API scraping
│   ├── custom_xml_scraper.py        # Manual XML parsing
│   ├── undetected_chrome_scraper.py # Bot detection bypass
│   └── template_validation_scraper.py # Template compliance
└── README.md
```

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

Required packages:
- `selenium` - Browser automation
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `openai` - AI-powered analysis
- `requests` - HTTP requests
- `nltk` - Natural language processing
- `lxml` - XML/HTML processing
- `htmlmin` - HTML minification
- `usp` - Sitemap parsing
- `undetected-chromedriver` - Anti-detection browser
- `tenacity` - Retry logic

### Configuration

1. **Set API Keys** in `constants.py`:
```python
OPENAI_API_KEY = "your-key-here"
LANG_TOOLS_UNAME = "your-username"
LANG_TOOLS_API_KEY = "your-key-here"
```

2. **Configure a Site** in `scraper_configs.py`:
```python
SCRAPER_CONFIGS = {
    "my_site": {
        "name": "my_site",
        "job_pattern": r"\/jobs\/\w+",
        "id_pattern": r"jobs\/(.+?)\/",
        "domain": "https://careers.example.com",
        "xpaths": [...]
    }
}
```
**Note on XPaths**: The default XPath payload is designed to extract the JD title, body text, and metadata section separately, so you'll want to use a webpage inspector to extract those and structure them in a way that won't be fragile to site changes.

### Basic Usage

```bash
# Basic scraping with XPath
python main.py -s BasicXPath

# API-based scraping with 30-day lookback
python main.py -s ApiWithAnalysis --lookback 30

# Resume from checkpoint
python main.py -s BasicXPath --checkpoint 1

# Development mode (skip expensive API calls)
python main.py -s BasicXPath -d 1
```

## 🔧 Scraper Types

### 1. BasicXPathScraper
**Use when**: Site has standard sitemap.xml and simple HTML structure

**Example**:
```bash
python main.py -s BasicXPath
```

---

### 2. ApiScraperWithAnalysis
**Use when**: Site exposes job listings API and you need custom business logic

**Features**:
- Session management with cookies
- Custom region/location mapping
- Template validation
- Extended metadata analysis

**Example**:
```bash
python main.py -s ApiWithAnalysis -l 30
```

---

### 3. GreenhouseApiScraper
**Use when**: Site uses Greenhouse ATS

**Features**:
- Direct Greenhouse API integration
- No authentication required
- Fast, reliable data extraction

**Example**:
```bash
python main.py -s GreenhouseApi
```

---

### 4. SessionApiScraper
**Use when**: API requires authentication and date-based filtering

**Features**:
- Persistent session management
- Date range filtering
- Pagination support
- Custom headers and cookies

**Example**:
```bash
python main.py -s SessionApi -l 14
```

---

### 5. CustomXmlScraper
**Use when**: Sitemap needs manual parsing or URL corrections

**Features**:
- Manual XML parsing with ElementTree
- URL transformation support
- WebDriverWait for dynamic content
- Namespace-agnostic XML handling

**Example**:
```bash
python main.py -s CustomXml
```

---

### 6. UndetectedChromeScraper
**Use when**: Site has aggressive bot detection (Cloudflare, etc.)

**Features**:
- Uses undetected-chromedriver
- Extended wait times
- Harder to detect as automated
- Sample/limiting mode for testing

**Example**:
```bash
python main.py -s UndetectedChrome
```

---

### 7. TemplateValidationScraper
**Use when**: Need to validate job postings against organizational standards

**Features**:
- Regex-based template validation
- Brand consistency checking
- Required sections verification

**Example**:
```bash
python main.py -s TemplateValidation
```

## 📊 Analysis Features

### Built-in Analysis (All Scrapers)

1. **Gender-Coded Language Detection**
   - Replication of academic research which found linguistic markers for candidate appeal based on gendered language.

2. **Grammar & Spelling**
   - LanguageTool API integration
   - Detailed issue categorization
   - Context-aware checking

3. **Structure Analysis**
   - Bullet point counting
   - Duplicate sentence detection

4. **LLM-Powered Analysis**
   - Salary listing compliance
   - JD structure summary (for later evaluation)
   - JD legibility evaluation
   - Candidate experience metrics:
     - proprietary markers for attracting the right hire

### Output Format

CSV file with columns:
```
url, title, job_desc, masculine_word_count, feminine_word_count,
grammar_mistakes, spelling_mistakes, section_headers,
pay_range_included, undefined_abbreviations,
contains_team_environment_context, contains_hiring_manager_context,
contains_future_goals_context, contains_work_environment_context,
contains_hiring_process_context, [custom_columns (as outlined in _run_company_analysis() and _run_company_post_processing())...]
```

## 🛠️ Development

### Adding a New Scraper

1. Create a new file in `scrapers/` inheriting from `ReportConstructor`
2. Override necessary methods:
   - `_process_sitemap()` - Custom sitemap processing
   - `_scrape_url()` - Custom page scraping
   - `_run_company_analysis()` - Client-specific data processing (template compliance, special analytical requests)
   - `_run_company_post_processing()` - Custom output formatting

3. Register in `main.py`:
```python
SCRAPER_CLASSES = {
    "MyNewScraper": MyNewScraper,
    # ...
}
```

### Checkpoint System

The framework automatically saves progress:
- `checkpoint.json` - Last scraped URL
- `data_checkpoint.json` - Scraped data payload

Resume with `--checkpoint 1` flag.

## 🎓 Use Cases

- **Compliance Detection**: Some checks are used to immediately surface JD's which are out-of-compliance (E.G. with pay disclosure requirements in some U.S. States).
- **Brand Consistency**: Ensure all postings follow templates
- **Candidate Experience**: Measure information transparency and markers for appeal.
- **Content Quality**: Monitor grammar, spelling, and readability
- **DEI Initiatives**: Identify gender-coded language

## ⚠️ Important Notes

### Ethics
- Only scrape publicly available job postings
- Respect site terms of service
- Don't overwhelm servers with requests
- Consider API limits and costs (OpenAI, LanguageTool)

### Development Mode
Use `-d 1` to skip expensive operations during testing:
- Skips OpenAI API calls
- Returns dummy data for data points relying on API calls
- Saves API costs during development

## 📝 A Note on Reuse

This is a portfolio project demonstrating web scraping, data analysis, and software engineering practices. Hence, I'm not bothering with a license. If you want to adapt it, I'm flattered; but please use it responsibly.