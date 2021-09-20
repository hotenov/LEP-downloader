"""App configuration module."""


ARCHIVE_URL = "https://hotenov.com"

LOCAL_ARCHIVE_HTML = "2021-08-10_lep-archive-page-content-pretty.html"

SHORT_LINKS_MAPPING_DICT = {
    "http://wp.me/p4IuUx-7PL": "https://teacherluke.co.uk/2017/06/20/460-catching-up-with-amber-paul-6-feat-sarah-donnelly/",
    "http://wp.me/p4IuUx-7C6": "https://teacherluke.co.uk/2017/04/25/444-the-rick-thompson-report-snap-general-election-2017/",
    "http://wp.me/p4IuUx-7C4": "https://teacherluke.co.uk/2017/04/21/443-the-trip-to-japan-part-2/",
    "http://wp.me/p4IuUx-7BQ": "https://teacherluke.co.uk/2017/04/21/442-the-trip-to-japan-part-1/",
    "http://wp.me/p4IuUx-7BO": "https://teacherluke.co.uk/2017/04/18/441-andy-johnson-at-the-iatefl-conference/",
    "http://wp.me/p4IuUx-7Av": "https://teacherluke.co.uk/2017/03/28/436-the-return-of-the-lying-game-with-amber-paul-video/",
    "http://wp.me/p4IuUx-7zK": "https://teacherluke.co.uk/2017/03/26/i-was-interviewed-on-my-fluent-podcast-with-daniel-goodson/",
    "http://wp.me/p4IuUx-7sg": "https://teacherluke.co.uk/2017/01/10/415-with-the-family-part-3-more-encounters-with-famous-people/",
    "https://wp.me/p4IuUx-29": "https://teacherluke.co.uk/2011/10/11/notting-hill-carnival-video-frustration-out-takes/",
}

# MISSPELLED_LTD = ".co.ukm"

IRRELEVANT_LINKS = (
        "https://wp.me/P4IuUx-82H",
)

EPISODE_LINK_RE = r"https?://((?P<short>wp\.me/p4IuUx-[\w-]+)|(teacherluke\.(co\.uk|wordpress\.com)/(?P<date>\d{4}/\d{2}/\d{2})/))"

LINK_TEXTS_MAPPING = {
    "https://teacherluke.co.uk/2018/04/18/522-learning-english-at-summer-school-in-the-uk-a-rambling-chat-with-raphael-miller/": \
        "522. Learning English at Summer School in the UK (A Rambling Chat with Raphael Miller)",

    "https://teacherluke.co.uk/2017/08/14/website-content-lukes-criminal-past-zep-episode-185/": \
        "[Website content] Luke’s Criminal Past (ZEP Episode 185)",

    "https://teacherluke.co.uk/2017/05/26/i-was-invited-onto-the-english-across-the-pond-podcast/": \
        "[Website content] I was invited onto the “English Across The Pond” Podcast",

    "https://teacherluke.co.uk/2016/03/20/i-was-invited-onto-craig-wealands-weekly-blab-and-we-talked-about-comedy-video/": \
        "[VIDEO] I was invited onto Craig Wealand’s weekly Blab, and we talked about comedy",
}
