
# early ref for the swedavia api

import json
import os
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.swedavia.se/flightinfo/v2"
PROBE_AIRPORT = "ARN"
PROBE_ENDPOINT = "departures"