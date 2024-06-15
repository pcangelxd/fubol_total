import httpx
from bs4 import BeautifulSoup
from dataclasses import asdict
from .models import LastMatches
from .util import (
    API_RESULTS_CONMEBOL,
    API_RESULTS_LALIGA,
    API_RESULTS_PREMIER_LEAGUE,
)
import logging

# Configurar el registro
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_match_statistics(_journeys: list, matches: BeautifulSoup):
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

            results[_journeys[journey_index]].append(asdict(data))
            date_index += 1

            if (i + 2) % 10 == 0:
                journey_index += 1

        return results

    except Exception as e:
        logger.error(f"Error processing match statistics: {e}")
        return {}

class Results(object):
    def __init__(self) -> None:
        self.api_urls = [
            API_RESULTS_CONMEBOL,
            API_RESULTS_LALIGA,
            API_RESULTS_PREMIER_LEAGUE,
            # Añadir más URLs según sea necesario
        ]
        self.results = {}

    def fetch_results(self, api_url):
        try:
            logger.debug(f"Fetching results from: {api_url}")
            response = httpx.get(api_url, timeout=10.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            section_journeys = soup.find('div', 'MatchCardsListsAppender_container__y5ame')

            if not section_journeys:
                logger.warning(f"No journeys found for URL: {api_url}")
                return {}

            _journeys = [journey.text for journey in section_journeys.find_all('div', 'SectionHeader_container__iVfZ9')]
            _matches = section_journeys.find_all('div', 'SimpleMatchCard_simpleMatchCard__content__ZWt2p')

            return get_match_statistics(_journeys, _matches)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return {}
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return {}
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {}

    @property
    def get_results(self):
        for api_url in self.api_urls:
            league_results = self.fetch_results(api_url)
            if league_results:
                self.results.update(league_results)
            else:
                logger.warning(f"No results fetched for URL: {api_url}")

        return self.results
