import os

import feedparser
import requests
from src.logger import Logger

logger = Logger().get_logger()

class Downloader:
    def download_feed(self, url: str):
        response = self._download(url)
        if response:
            feed = feedparser.parse(response.content)
            if feed.bozo:
                logger.error(f"Error parsing feed: {feed.bozo_exception}")
                return None
            return feed
        return None

    def download_feed_on_disk(self, url: str, path: str):
        response = self._download(url)
        if response:
            feed = feedparser.parse(response.content)
            if feed.bozo:
                logger.error(f"Error parsing feed: {feed.bozo_exception}")
                return None

            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as file:
                    file.write(response.content)

                logger.info(f"Feed saved successfully at {path}")
                return feed
            except IOError as e:
                logger.exception(f"Error saving the feed to disk: {e}")
                return None
        return None

    @staticmethod
    def _download(url: str):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            return response
        except requests.exceptions.RequestException as e:
            logger.exception(f"Error downloading data: {e}")
            return None


def main():
    downloader = Downloader()
    rss_url = "https://feeds.simplecast.com/8W_aZ33f"
    feed = downloader.download_feed(rss_url)


if __name__ == "__main__":
    main()
