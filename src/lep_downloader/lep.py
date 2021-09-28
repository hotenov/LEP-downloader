"""LEP module for general logic and classes."""


class LepEpisode:
    """LEP episode class."""

    def __init__(
        self,
        episode: int = 0,
        date: str = "2000-01-01T00:00:00+00:00",
        url: str = "",
        post_title: str = "",
        parsing_utc: str = "",
        index: int = 0,
        admin_note: str = "",
    ) -> None:
        """Default instance of LepEpisode.

        Args:
            episode (int): Episode number.
            date (str): Post datetime (default 2000-01-01T00:00:00+00:00).
            url (str): Final location of post URL.
            post_title (str): Post title, extracted from tag <a> and safe for windows path.
            parsing_utc (str): Parsing datetime in UTC timezone (with microseconds).
            index (int): Parsing index: concatenation of URL date and increment (for several posts).
            admin_note (str): Note for administrator and storing error message (for bad response)
        """
        self.episode = episode
        self.date = date
        self.url = url
        self.post_title = post_title
        self.parsing_utc = parsing_utc
        self.index = index
        self.admin_note = admin_note
