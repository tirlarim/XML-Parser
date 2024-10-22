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

    def download_feed_on_disk(self, url: str, save_path: str):
        response = self._download(url)
        if response:
            feed = feedparser.parse(response.content)
            if feed.bozo:
                logger.error(f"Error parsing feed: {feed.bozo_exception}")
                return None

            try:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as file:
                    file.write(response.content)

                logger.info(f"Feed saved successfully at {save_path}")
                return feed
            except IOError as e:
                logger.exception(f"Error saving the feed to disk: {e}")
                return None
        return None

    def download_mp3s_from_feed(self, feed, download_directory: str):
        if not feed or 'entries' not in feed:
            logger.error("No entries in feed to download MP3 files.")
            return

        os.makedirs(download_directory, exist_ok=True)

        for entry in feed.entries:
            links = entry.get("links", None)
            if links is None:
                logger.error("No Links in Feed")
            for link in entry["links"]:
                if link.get('type') == 'audio/mpeg':
                    guid = entry.get('id', None)
                    mp3_url = link.get('href')
                    mp3_file_name = f"{guid}.mp3"
                    if not guid:
                        logger.error("No GUID found for entry; skipping MP3 download.")
                        continue
                    mp3_file_path = os.path.join(download_directory, mp3_file_name)
                    self.download_mp3(mp3_url, mp3_file_path)

    def download_mp3(self, mp3_url: str, save_path: str):
        if os.path.exists(save_path):
            logger.info(f"MP3 file already exists at {save_path}, skipping download.")
            return True
        response = self._download(mp3_url)
        if response:
            try:
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                logger.info(f"MP3 file saved successfully at {save_path}")
                return True
            except IOError as e:
                logger.exception(f"Error saving MP3 file to disk: {e}")
                return False
        return False

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
    downloader.download_mp3s_from_feed(feed, "media/audio")


if __name__ == "__main__":
    main()
