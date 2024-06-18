import httpx
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            
            # This is where you define the specific classes or ids of the images you're looking for
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


if __name__ == "__main__":
    url = "https://lordsmobilecartograph.ru/Kingdom?K=959"
    scraper = ImageScraper(url)
    images = scraper.fetch_images()
    for name, link in images.items():
        print(f"{name}: {link}")
