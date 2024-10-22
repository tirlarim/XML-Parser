from src.downloader import Downloader
from src.feed_printer import RSSFeedPrinter
from src.logger import Logger

logger = Logger().get_logger()


def main():
    rss_url = "https://feeds.simplecast.com/8W_aZ33f"
    downloader = Downloader()
    printer = RSSFeedPrinter("./configs/printer.ini")
    feed = downloader.download_feed(rss_url)
    if feed is None:
        return
    printer.print_feed(feed)
    downloader.download_mp3s_from_feed(feed, "./media/audio")


if __name__ == "__main__":
    main()
