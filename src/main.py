import os

from dotenv import load_dotenv

from src.downloader import Downloader
from src.feed_printer import RSSFeedPrinter
from src.logger import Logger
from src.pgdb import PostgresDB

logger = Logger().get_logger()

load_dotenv()


def main():
    rss_url = "https://feeds.simplecast.com/8W_aZ33f"
    downloader = Downloader()
    db = PostgresDB()
    printer = RSSFeedPrinter("./configs/printer.ini")

    feed = downloader.download_feed(rss_url)
    if feed is None:
        return
    printer.print_feed(feed)

    db.create_cv_tables(drop=bool(int(os.getenv('PG_DEBUG', '0'))))  # Be careful with drop in production
    db.insert_items(feed)

    downloader.download_mp3s_from_feed(feed, "./media/audio")


if __name__ == "__main__":
    main()
