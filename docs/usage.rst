Usage Examples
==============

.. meta::
   :description: Usage Examples. How to download all LEP episodes using Python 3.8+
   :keywords: english, podcast, LEP, downloader, episodes, app, quick start, usage


.. important::
   There are some definitions which are used in this guide:

   **app folder** - folder (directory) where ``lep-downloader.exe`` is located (installed)

   **destination folder** - folder (directory) where downloaded files (.mp3, .pdf)
   will be saved. By default it's the same as *app folder*

Full list of script options you can find on `Man Page`_.

For all commands in this guide,
you can substitute script name ``lep-downloader`` with its short version ``lep-dl``.
Also it's implied that:

* all episodes (and database) are available;
* you have not downloaded these episodes before;
* you answer "Yes" for download confirmation.

=========

How to download episode by its number
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get certain episode, run script with ``--episode`` option:

.. code:: none

   lep-downloader --episode 707

or with short one:

.. code:: none

   lep-downloader -ep 707

Episode (mp3 file) will be downloaded to the **app folder**.

How to change destination folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For saving files to more familiar location,
you can specify destination folder with ``--dest`` option:

.. code:: none

   lep-downloader -ep 707 --dest "C:\English\podcasts\LEP"

If path is writable, episode will be downloaded to this folder.
Otherwise, '*Error: Invalid value...*' will be displayed.

Option has short version ``-d``

.. code:: none

   lep-downloader -ep 707 -d "C:/English/podcasts/LEP"


.. note::
   On Windows, you can use both path style:
   with back slash (native), or with forward slash.
   
   On MacOS and Linux, forward slash is more preferable.

   All intermediate sub-directories for destination folder
   will be created automatically. You don't have to worry about it.


How to download episode by its date
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you know exact day when episode was posted on archive page,
you can specify date interval like this:

.. code:: none

   lep-downloader -S 2019-09-17 -E 2019-09-17 -d "C:/English/podcasts/LEP"

Episode #615 will be downloaded.

All episodes for year 2011:

.. code:: none

   lep-downloader -S 2011-01-01 -E 2011-12-31 -d "C:/English/podcasts/LEP"


You can specify only one of the bounds (start or end).
In this case another bound will be set with default value
(first episode ever or the last episode at running moment).
For example, let's download all episodes starting from *2022*:

.. code:: none

   lep-downloader -S 2022-01-01 --dest "C:\English\podcasts\LEP"

How to download a range of episodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's assume that you've skipped episodes from 707 to 711.
You can download them with one command:

.. code:: none

   lep-downloader -ep 707-711 -d "C:\English\podcasts\LEP"

All five episodes will be downloaded.

You can omit one bound leaving hyphen:

.. code:: none

   lep-downloader --episode 755- -d "C:\English\podcasts\LEP"

All episodes from #755 to last will be downloaded.
The same story for ``-ep -10`` (episodes from first to #10).

.. note::
   If you specify range option \--episode / -ep
   and date filter option -S / -E together ->
   **range option will be ignored**.
   
   You **cannot** specify random (comma separated range),
   i.e. ``-ep 3,117,513`` is invalid option value.


How to download the last episode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: none

   lep-downloader --last -d "C:\English\podcasts\LEP"


How to download PDF along with MP3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each episode web page has been exported to PDF file
*(don't confuse with separate transcript file)*.
You can download it along with episode audio file (.mp3)
using this command:

.. code:: none

   lep-downloader -ep 122 --with-pdf -d "C:\English\podcasts\LEP"

or with short ``-pdf``

.. hint::
   You can specify options in any order as you like.

.. code:: none

   lep-downloader -d "C:\English\podcasts\LEP" -pdf --last 

If you want to download PDF files for all "TEXT" episodes (without any audio),
you should combine two options:

.. code:: none

   lep-downloader -ep 0-0 -pdf -d "C:\English\podcasts\LEP"

Such episodes have number = **0** under the hood,
that's why we've set range ``0-0`` in this command.


How to download all episodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's very simple. Run script without options.
For convenience, specify only destination folder:

.. code:: none

   lep-downloader -d "C:\English\podcasts\LEP"

.. attention::
   Be careful, running this command.

   ALL episodes (audio + pdf) will take up more than 40 GB
   on your drive (HDD, SSD, flash)
   *(relevant on moment when #758 is the latest episode)*
   and process of downloading will take at least ~4 hours
   (depends on the speed of Internet connection).
   You must have enough free space for downloading all of them.

=========

.. hint::
   Did not find your answer? Let me know about it by
   creating a new `Discussion`_
   or writing me a letter to qa[at]hotenov.com

.. _Man Page: manpage.html
.. _Discussion: https://github.com/hotenov/LEP-downloader/discussions
