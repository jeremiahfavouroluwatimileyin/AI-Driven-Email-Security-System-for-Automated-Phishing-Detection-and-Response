# Central configuration file for Wizard

import os
from dotenv import load_dotenv

# Load .env file when running locally
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4.1-mini"

# Company info used in delegations and responses
COMPANY_NAME = "Tech Solutions"
USER_NAME = "Jeremiah Favour"
USER_EMAIL = "jeremiahfavouroluwatimileyin@gmail.com"

# Internal email addresses for delegation
DELEGATION_TARGETS = {
    "HR": "hr@techsolutions.com",
    "Security": "headofsecurity@techsolutions.com",
    "Finance": "finance@techsolutions.com",
    "Legal": "legal@techsolutions.com",
    "IT": "it@techsolutions.com",
    "Management": "management@techsolutions.com",
}

# Gmail OAuth scopes
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Max emails to fetch from Gmail at once
GMAIL_MAX_RESULTS = 20