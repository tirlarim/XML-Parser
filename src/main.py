from src.downloader import Downloader
from src.feed_printer import RSSFeedPrinter
from src.logger import Logger

logger = Logger().get_logger()

def main():
    rss_url = "https://feeds.simplecast.com/8W_aZ33f"
    printer = RSSFeedPrinter("./configs/printer.ini")
    feed = Downloader().download_feed(rss_url)
    if feed is None:
        return
    printer.print_feed(feed)


if __name__ == "__main__":
    main()
