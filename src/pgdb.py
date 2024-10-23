import os
import uuid
from datetime import datetime
from functools import wraps

import psycopg2
from dotenv import load_dotenv
from psycopg2 import OperationalError, InterfaceError
from psycopg2 import pool

from src.downloader import Downloader
from src.feed_printer import RSSFeedPrinter
from src.logger import Logger

load_dotenv()

logger = Logger().get_logger()

DEBUG = bool(int(os.getenv('PG_DEBUG', '0')))


class PostgresDB:
    _connection_pull_min_count: int = 5
    _connection_pull_max_count: int = 10
    _db_pool: pool.ThreadedConnectionPool | None = None

    def __init__(self):
        self._create_connection_pull()
        self.ping()

    def __exit__(self, exc_type, exc_value, traceback):
        self._close_connection_pull()

    # Decorators section

    @staticmethod
    def with_db_connection(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            connection = None
            try:
                connection = self._db_pool.getconn()
                try:
                    with connection.cursor() as cursor:  # self.ping()
                        cursor.execute('SELECT version();')
                        db_version = cursor.fetchone()
                        logger.info(f"Ping: Connected to PostgreSQL Database. Version: {db_version}")
                except (OperationalError, InterfaceError) as e:
                    logger.warning("Initial connection check failed, attempting to reset connection: %s", e)
                    self._db_pool.putconn(connection, close=True)
                    connection = self._db_pool.getconn()  # Attempt to get a new connection from the pool
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")  # Re-check the new connection
                return func(self, connection, *args, **kwargs)
            except Exception as e:
                logger.exception("Exception in with_db_connection decorator: %s", e)
                if connection:  # Close the connection on any unexpected error
                    self._db_pool.putconn(connection, close=True)
                    connection = None
                raise
            finally:
                if connection:
                    self._db_pool.putconn(connection, close=True)

        return wrapper

    # Public section

    @with_db_connection
    def ping(self, connection):
        cursor = connection.cursor()
        cursor.execute('SELECT version();')
        db_version = cursor.fetchone()
        logger.info(f"Ping: Connected to PostgreSQL Database. Version: {db_version}")
        cursor.close()

    @with_db_connection
    def create_cv_tables(self, connection, drop: bool = False):
        cursor = connection.cursor()
        if drop:
            cursor.execute("""
            DROP TABLE IF EXISTS
            podcast_item, podcast_author, podcast_keyword, podcast_author_map, podcast_keyword_map
            CASCADE;
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS podcast_item (
            id SERIAL,
            guid UUID UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            pub_date TIMESTAMP,
            link TEXT,
            content_encoded TEXT,
            enclosure_length BIGINT,
            enclosure_type TEXT,
            enclosure_url TEXT,
            itunes_title TEXT,
            itunes_duration INTERVAL,
            itunes_summary TEXT,
            itunes_subtitle TEXT,
            itunes_explicit BOOLEAN,
            itunes_episode_type TEXT,
            itunes_episode INT,
            PRIMARY KEY(id)
        );
        CREATE TABLE IF NOT EXISTS podcast_author (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS podcast_keyword (
            id SERIAL PRIMARY KEY,
            keyword TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS podcast_author_map (
            podcast_item_id INT REFERENCES podcast_item(id) ON DELETE CASCADE,
            author_id INT REFERENCES podcast_author(id) ON DELETE CASCADE,
            PRIMARY KEY (podcast_item_id, author_id)
        );
        CREATE TABLE IF NOT EXISTS podcast_keyword_map (
            podcast_item_id INT REFERENCES podcast_item(id) ON DELETE CASCADE,
            keyword_id INT REFERENCES podcast_keyword(id) ON DELETE CASCADE,
            PRIMARY KEY (podcast_item_id, keyword_id)
        )
        """)
        connection.commit()
        cursor.close()

    @with_db_connection
    def insert_items(self, connection, feed):
        cursor = connection.cursor()

        check_existing_podcast_item = """
        SELECT id FROM podcast_item WHERE guid = %s;
        """

        insert_podcast_item = """
        INSERT INTO podcast_item (
            guid, title, description, pub_date, link, content_encoded,
            enclosure_length, enclosure_type, enclosure_url, itunes_title,
            itunes_duration, itunes_summary, itunes_subtitle, itunes_explicit,
            itunes_episode_type, itunes_episode
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        insert_author = """
        INSERT INTO podcast_author (name) VALUES (%s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id;
        """

        insert_keyword = """
        INSERT INTO podcast_keyword (keyword) VALUES (%s)
        ON CONFLICT (keyword) DO NOTHING
        RETURNING id;
        """

        insert_podcast_author_map = """
        INSERT INTO podcast_author_map (podcast_item_id, author_id)
        VALUES (%s, %s);
        """

        insert_podcast_keyword_map = """
        INSERT INTO podcast_keyword_map (podcast_item_id, keyword_id)
        VALUES (%s, %s);
        """

        for entry in feed.entries:  # TODO: rewrite with executemany()
            guid = entry.guid
            normalized_guid = str(uuid.UUID(guid))
            cursor.execute(check_existing_podcast_item, (normalized_guid,))
            existing_item = cursor.fetchone()
            if existing_item:
                logger.info(f"Item with UUID {normalized_guid} is already saved. Skipped.")
                continue
            title = entry.title
            description = entry.description if 'description' in entry else None
            pub_date = datetime.strptime(entry.published,
                                         '%a, %d %b %Y %H:%M:%S %z').isoformat() if 'published' in entry else None
            link = entry.link if 'link' in entry else None
            content_encoded = entry.content[0].value if 'content' in entry else None
            enclosure = entry.enclosures[0] if 'enclosures' in entry and entry.enclosures else {}
            enclosure_length = enclosure.get('length', None)
            enclosure_type = enclosure.get('type', None)
            enclosure_url = enclosure.get('url', None)
            itunes_title = entry.itunes_title if 'itunes_title' in entry else None
            itunes_duration = entry.itunes_duration if 'itunes_duration' in entry else None
            itunes_summary = entry.summary if 'summary' in entry else None
            itunes_subtitle = entry.subtitle if 'subtitle' in entry else None
            itunes_explicit = entry.itunes_explicit == 'true' if 'itunes_explicit' in entry else None
            itunes_episode_type = entry.itunes_episodetype if 'itunes_episodetype' in entry else None  # NOTE: itunes_episodetype is not a typo
            itunes_episode = entry.itunes_episode if 'itunes_episode' in entry else None
            cursor.execute(insert_podcast_item, (
                normalized_guid, title, description, pub_date, link, content_encoded,
                enclosure_length, enclosure_type, enclosure_url, itunes_title,
                itunes_duration, itunes_summary, itunes_subtitle, itunes_explicit,
                itunes_episode_type, itunes_episode
            ))
            podcast_item_id = cursor.fetchone()[0]
            authors = entry.author.split(", ") if 'author' in entry else []
            for author in authors:
                cursor.execute(insert_author, (author,))
                author_id = cursor.fetchone()
                if author_id is None:
                    cursor.execute("SELECT id FROM podcast_author WHERE name = %s;", (author,))
                    author_id = cursor.fetchone()[0]
                else:
                    author_id = author_id[0]
                cursor.execute(insert_podcast_author_map, (podcast_item_id, author_id))

            # Insert keywords and map them to the podcast item
            keywords = entry.tags if 'tags' in entry else []
            for keyword in keywords:
                keyword = keyword["term"]
                cursor.execute(insert_keyword, (keyword,))
                keyword_id = cursor.fetchone()
                if keyword_id is None:
                    cursor.execute("SELECT id FROM podcast_keyword WHERE keyword = %s;", (keyword,))
                    keyword_id = cursor.fetchone()[0]
                else:
                    keyword_id = keyword_id[0]
                cursor.execute(insert_podcast_keyword_map, (podcast_item_id, keyword_id))

        connection.commit()
        cursor.close()

    @with_db_connection
    def delete_item(self, connection, applicant_uuid: str):
        cursor = connection.cursor()
        try:
            delete_query = """
            DELETE FROM podcast_item
            WHERE guid = %s;
            """
            cursor.execute(delete_query, (applicant_uuid,))
            connection.commit()
            if cursor.rowcount > 0:
                print(f"Item with UUID {applicant_uuid} successfully deleted.")
            else:
                print(f"No item found with UUID {applicant_uuid}.")

        except (Exception, psycopg2.DatabaseError) as error:
            connection.rollback()
            print(f"Error occurred: {error}")
        finally:
            cursor.close()

    # Private section

    def _create_connection_pull(self):
        try:
            if not DEBUG:  # here should be pool to production DB
                self._db_pool = pool.ThreadedConnectionPool(
                    minconn=self._connection_pull_min_count,
                    maxconn=self._connection_pull_max_count,
                    host=os.getenv('PG_HOST'),
                    port=os.getenv('PG_PORT'),
                    database=os.getenv('PG_DB_NAME'),
                    user=os.getenv('PG_LOGIN'),
                    password=os.getenv('PG_PASS')
                )
            else:  # here should be pool to local, debug DB
                self._db_pool = pool.ThreadedConnectionPool(
                    minconn=self._connection_pull_min_count,
                    maxconn=self._connection_pull_max_count,
                    host=os.getenv('PG_HOST_DEBUG'),
                    port=int(os.getenv('PG_PORT_DEBUG')),
                    database=os.getenv('PG_NAME_DEBUG'),
                    user=os.getenv('PG_LOGIN_DEBUG'),
                )
            if self._db_pool is None:
                logger.exception('Unable to connect to database')
        except OperationalError as e:
            self._db_pool = None
            logger.exception(
                f"The error '{e}' occurred while trying to create connection pull to the PostgreSQL Database.")
        except Exception as e:
            logger.exception(
                f"An error occurred while trying to create connection pull to the PostgreSQL Database. {e}")

    def _close_connection_pull(self):
        if self._db_pool is not None and not self._db_pool.closed:
            self._db_pool.closeall()
            print("Database connection pull closed.")


def upload_all():
    db = PostgresDB()
    # db.delete_item("8a645486-2b2b-46d0-97fe-61afeb49a1af") # can be uncomented to test delete
    db.create_cv_tables(drop=DEBUG)  # Be careful with drop in production
    rss_url = "https://feeds.simplecast.com/8W_aZ33f"
    downloader = Downloader()
    printer = RSSFeedPrinter("./configs/printer.ini")
    feed = downloader.download_feed(rss_url)
    if feed is None:
        logger.error("Feed is None")
        return
    printer.print_feed(feed)
    db.insert_items(feed)


if __name__ == "__main__":
    upload_all()
