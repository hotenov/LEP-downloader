"""LEP module for general logic and classes."""
import json
import typing as t


class LepEpisode(object):
    """LEP episode class."""

    def __init__(
        self,
        episode: int = 0,
        date: str = "2000-01-01T00:00:00+00:00",
        url: str = "",
        post_title: str = "",
        post_type: str = "",
        parsing_utc: str = "",
        index: int = 0,
        audios: t.Optional[t.List[t.List[str]]] = None,
        admin_note: str = "",
    ) -> None:
        """Default instance of LepEpisode.

        Args:
            episode (int): Episode number.
            date (str): Post datetime (default 2000-01-01T00:00:00+00:00).
            url (str): Final location of post URL.
            post_title (str): Post title, extracted from tag <a> and safe for windows path.
            post_type (str): Post type ("AUDIO", "TEXT", etc.).
            audios (list): List of links lists (for multi-part episodes).
            parsing_utc (str): Parsing datetime in UTC timezone (with microseconds).
            index (int): Parsing index: concatenation of URL date and increment (for several posts).
            admin_note (str): Note for administrator and storing error message (for bad response)
        """
        self.episode = episode
        self.date = date
        self.url = url
        self.post_title = post_title
        self.post_type = post_type
        self.audios = audios
        self.parsing_utc = parsing_utc
        self.index = index
        self.admin_note = admin_note


class LepJsonEncoder(json.JSONEncoder):
    """Custom JSONEncoder for LepEpisode objects."""

    def default(self, obj: t.Any) -> t.Any:
        """Override 'default' method for encoding JSON objects."""
        if isinstance(obj, LepEpisode):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
