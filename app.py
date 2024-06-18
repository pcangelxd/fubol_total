import json
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import httpx
from bs4 import BeautifulSoup
from dataclasses import asdict
import logging
from exceptions import page_not_found, internal_server_error

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

API_RESULTS_CONMEBOL = 'https://onefootball.com/es/competicion/conmebol-eliminatorias-copa-mundial-74/resultados'
API_RESULTS_LALIGA = 'https://onefootball.com/es/competicion/laliga-10/resultados'
API_RESULTS_PREMIER_LEAGUE = 'https://onefootball.com/es/competicion/premier-league/resultados'

app = Flask(__name__)
CORS(app)

app.register_error_handler(404, page_not_found)
app.register_error_handler(500, internal_server_error)

def render_json(_object: dict):
    response = app.response_class(
        response=json.dumps(_object),
        status=200,
        mimetype='application/json'
    )
    return response

class LastMatches:
    def __init__(self, first_team, second_team, winner, date):
        self.first_team = first_team
        self.second_team = second_team
        self.winner = winner
        self.date = date

    def to_dict(self):
        return asdict(self)

class Results:
    def __init__(self, api_url):
        self.api_url = api_url
        self.results = {}

    def fetch_results(self):
        try:
            response = httpx.get(self.api_url, timeout=10.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            section_journeys = soup.find('div', 'MatchCardsLists
