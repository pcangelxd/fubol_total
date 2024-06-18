import json
import time
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import httpx
from bs4 import BeautifulSoup
import logging
from exceptions import page_not_found, internal_server_error

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

class ImageScraper:
    def __init__(self, url):
        self.url = url
        self.images = {}

    def fetch_images(self):
        try:
            logger.debug(f"Fetching images from: {self.url}")
            response = httpx.get(self.url, timeout=10.0)
            response.raise_for_status()
            
            # Pausar la ejecución por 20 segundos para permitir que la página cargue completamente
            logger.debug("Waiting for 20 seconds to let the page load completely...")
            time.sleep(20)

            soup = BeautifulSoup(response.content, "html.parser")
            image_elements = soup.find_all('img', {'class': 'image-event-main border-box-main'})
            
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

@app.route('/api/images')
def fetch_images():
    try:
        url = "https://lordsmobilecartograph.ru/Kingdom?K=959"
        scraper = ImageScraper(url)
        images = scraper.fetch_images()
        return render_json(images)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
