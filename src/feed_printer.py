import configparser

import colorama

from src.downloader import Downloader, logger


class RSSFeedPrinter:
    def __init__(self, config_file=None):
        colorama.init(autoreset=True)
        self.fields_to_print = None
        self.colors = {}
        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        self.fields_to_print = config.get('Settings', 'fields', fallback=None)
        if self.fields_to_print:
            self.fields_to_print = self.fields_to_print.split(',')

        if config.has_section('Colors'):
            for field, color in config.items('Colors'):
                self.colors[field] = color

    def print_feed(self, feed):
        if not feed:
            logger.error("No feed to display")
            return

        # Feed-level meta
        logger.info("Feed Info:")
        logger.info(f"Title: {feed.feed.get('title', 'N/A')}")
        logger.info(f"Link: {feed.feed.get('link', 'N/A')}")
        logger.info(f"Description: {feed.feed.get('description', 'N/A')}")
        logger.info(f"Copyright: {feed.feed.get('copyright', 'N/A')}")
        logger.info(f"Lang: {feed.feed.get('language', 'N/A')}")

        for entry in feed.entries:
            if self.fields_to_print:
                for key in self.fields_to_print:
                    color = self.colors.get(key, None)
                    value = entry.get(key, None)
                    if value is None:
                        logger.warning(f"Unable to find {key} key in entry. Skipped.")
                        continue
                    if color:
                        self._print_with_color(key, value, color)
                    else:
                        logger.info(f"{key}: {value}")
            else:
                defaultMeta = {
                    "title": entry.get("title", "N/A"),
                    "author": entry.get("author", "N/A"),
                    "link": entry.get("link", "N/A"),
                    "published": entry.get("published", "N/A"),
                    "summary": entry.get("summary", "N/A")
                }
                for key, value in defaultMeta.items():
                    logger.info(f"{key}: {value}")

    @staticmethod
    def _print_with_color(key, value, color):
        color_map = {
            'red': colorama.Fore.RED,
            'green': colorama.Fore.GREEN,
            'yellow': colorama.Fore.YELLOW,
            'blue': colorama.Fore.BLUE,
        }
        color_code = color_map.get(color, colorama.Style.RESET_ALL)
        logger.info(f"{color_code}{key}: {value}{colorama.Style.RESET_ALL}")


def example_use():
    rss_url = "https://feeds.simplecast.com/8W_aZ33f"
    printer = RSSFeedPrinter()
    feed = Downloader().download_feed(rss_url)
    printer.print_feed(feed)
    logger.info("\n----\n")
    printer_with_config = RSSFeedPrinter("./configs/printer.ini")
    feed_with_config = Downloader().download_feed(rss_url)
    printer_with_config.print_feed(feed_with_config)


if __name__ == "__main__":
    example_use()
