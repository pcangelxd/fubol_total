import json
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import httpx
from bs4 import BeautifulSoup
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
            section_journeys = soup.find('div', 'MatchCardsListsAppender_container__y5ame')

            if not section_journeys:
                return {}

            _journeys = [journey.text for journey in section_journeys.find_all('div', 'SectionHeader_container__iVfZ9')]
            _matches = section_journeys.find_all('div', 'SimpleMatchCard_simpleMatchCard__content__ZWt2p')

            self.results = self.get_match_statistics(_journeys, _matches)
            return self.results
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error occurred: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

    def get_match_statistics(self, _journeys: list, matches: BeautifulSoup):
        try:
            team_names = [x.text for team in matches for x in team.find_all('span', 'SimpleMatchCardTeam_simpleMatchCardTeam__name__7Ud8D')]
            goals = [x.text for team in matches for x in team.find_all('span', 'SimpleMatchCardTeam_simpleMatchCardTeam__score__UYMc_')]
            match_dates = [x.find('time').get('datetime') for team in matches for x in team.find_all('div', 'SimpleMatchCard_simpleMatchCard__matchContent__prwTf')]

            results = {}
            date_index = 0
            journey_index = 0

            for i in range(0, len(team_names), 2):
                if i + 1 >= len(team_names) or date_index >= len(match_dates):
                    break  # Evitar acceso fuera del rango

                first_team = {'country': team_names[i], 'goals': goals[i] if i < len(goals) else '0'}
                second_team = {'country': team_names[i + 1], 'goals': goals[i + 1] if i + 1 < len(goals) else '0'}
                winner = 'Tie' if goals[i] == goals[i + 1] else team_names[i] if goals[i] > goals[i + 1] else team_names[i + 1]
                date = match_dates[date_index]

                data = LastMatches(
                    first_team=first_team,
                    second_team=second_team,
                    winner=winner,
                    date=date
                )

                if _journeys[journey_index] not in results:
                    results[_journeys[journey_index]] = []

                results[_journeys[journey_index]].append(data.to_dict())
                date_index += 1

                if (i + 2) % 10 == 0:
                    journey_index += 1

            return results

        except Exception as e:
            return {"error": f"Error processing match statistics: {e}"}

class ImageScraper:
    def __init__(self, url):
        self.url = url
        self.images = {}

    def fetch_images(self):
        try:
            logger.debug(f"Fetching images from: {self.url}")
            response = httpx.get(self.url, timeout=10.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            image_elements = soup.find_all('img')
            
            if not image_elements:
                logger.warning(f"No images found for URL: {self.url}")
                return {}

            self.images = self.extract_images(image_elements)
            return self.images
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return {}
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return {}
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {}

    def extract_images(self, image_elements):
        try:
            images = {}
            for index, img in enumerate(image_elements):
                img_src = img.get('src')
                if img_src and 'events/factor' in img_src:  # Filtrar imágenes específicas
                    img_name = f"image_{index + 1}"
                    images[img_name] = img_src
                    logger.debug(f"Found image: {img_name} -> {img_src}")

            return images
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/results/conmebol')
def results_conmebol():
    try:
        results = Results(API_RESULTS_CONMEBOL).fetch_results()
        return render_json(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/results/laliga')
def results_laliga():
    try:
        results = Results(API_RESULTS_LALIGA).fetch_results()
        return render_json(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/results/premier-league')
def results_premier_league():
    try:
        results = Results(API_RESULTS_PREMIER_LEAGUE).fetch_results()
        return render_json(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/images')
def fetch_images():
    try:
        url = "https://lordsmobilecartograph.ru/Kingdom?K=959"
        scraper = ImageScraper(url)
        images = scraper.fetch_images()
        return render_json(images)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
