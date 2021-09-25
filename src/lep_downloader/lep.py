"""LEP module for general logic and classes."""


class LepEpisode:
    """LEP episode class."""

    def __init__(
        self,
        episode: int = 0,
        date: str = "2000-01-01T00:00:00+00:00",
        url: str = "",
        post_title: str = "",
        index: int = 0,
    ) -> None:
        """Default instance of LepEpisode.

        Args:
            episode (int): Episode number.
            date (str): Post datetime (default 2000-01-01T00:00:00+00:00).
            url (str): Final location of post URL.
            post_title (str): Post title, extracted from tag <a> and safe for windows path.
            index (int): Parsing index: concatenation of URL date and increment (for several posts).
        """
        self.episode = episode
        self.date = date
        self.url = url
        self.post_title = post_title
        self.index = index
