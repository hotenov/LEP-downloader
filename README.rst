LEP Downloader
==============

.. badges-begin

|PyPI| |Status| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/lep-downloader.svg
   :target: https://pypi.org/project/lep-downloader/
   :alt: PyPI
.. |Status| image:: https://img.shields.io/pypi/status/lep-downloader.svg
   :target: https://pypi.org/project/lep-downloader/
   :alt: Status
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/lep-downloader
   :target: https://pypi.org/project/lep-downloader
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/lep-downloader
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/lep-downloader/latest.svg?label=Read%20the%20Docs
   :target: https://lep-downloader.readthedocs.io/
   :alt: Read the documentation at https://lep-downloader.readthedocs.io/
.. |Tests| image:: https://github.com/hotenov/lep-downloader/workflows/Tests/badge.svg
   :target: https://github.com/hotenov/lep-downloader/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/hotenov/lep-downloader/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/hotenov/lep-downloader
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black

=========

.. badges-end

.. raw:: html

   <p align="center"><img alt="logo" src="docs/_static/logo.png" width="40%" /></p>
   <p align="center">
      📚
      <a href="https://lep-downloader.readthedocs.io" target="_blank">
         Read the full documentation
      </a>
      📚
   </p>


.. after-image

About
------

LEP Downloader is a script for downloading the all FREE episodes of `Luke's ENGLISH Podcast`_.

It lets you to get all audio files (including audio tracks to video episodes)
and also PDF files for each episode page.

Even though this script was written for convenient episode downloading,
I don't want to financially harm Luke in any way.
I just want to make my life a bit easier (as usual for lazy IT person =).
So consider `donating`_ to Luke's English Podcast and `becoming`_ his premium subscriber.


🚀 Features
-------------

* Download a range of episodes filtering by episode number or by episode date
* Download only the last episode
* Download PDF files of episodes web pages
* Saving files to specified folder on your hard / solid / flash drive
* Running script in quiet mode for automated routine
* Writing log file in debug mode


🛠️ Requirements
----------------

* Python 3.8+
* Internet connection


💻 Installation
----------------

You can install *LEP Downloader* via pip_ from PyPI_:

.. code:: none

   pip install lep-downloader

I do recommend you to use pipx_ for any CLI Python package.
It let you install and run Python applications in isolated environments.

.. code:: none

   python -m pip install --user pipx
   pipx install lep-downloader
   lep-downloader --help


🕹 Usage
--------

.. code:: none

   lep-downloader -ep 758

You can also use the short script name:

.. code:: none

   lep-dl --last

Please see the `Usage Examples <Usage_>`_ for details.

Or skim the `Man Page <Manpage_>`_ for available options
(if terminal is your best friend).


✨ What's new in version 3
---------------------------

The third version was completely re-written by me (again).
But this time with more fundamental and mature approach.
I applied some OOP (object-oriented programming) principles
and covered almost all functions with absolutely isolated unit tests.

Code base became more extendable and maintainable *(I believe)*.
I dropped support for file naming from old script versions.
Also I removed (for awhile) video and add-ons download
*(I plan to add them again in the future, however - no any promises)*.

Archive parsing was improved (without skipping several episodes).
Also I added built-in possibility to download files from reserve server,
if primary link is not available (for any reason).

And many internal little things.
You can read descriptions of pre-releases on `Releases`_ page (if you wish).


✊ Contributing
---------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


📝 License
-----------

Distributed under the terms of the `MIT license <https://opensource.org/licenses/MIT>`_,
*LEP Downloader* is free and open source software.
It means you can modify it, redistribute it or use it however you like
as long as you do mention the author of the original script.


🐞 Issues
----------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


🙏🏻 Credits
------------

This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

Script uses the following packages / libraries under the hood:

* `click <https://github.com/pallets/click>`_ (`BSD-3-Clause License <https://github.com/pallets/click/blob/main/LICENSE.rst>`__)
* `requests <https://github.com/psf/requests>`_ (`Apache-2.0 License <https://github.com/psf/requests/blob/main/LICENSE>`__)
* `beautifulsoup4 <https://www.crummy.com/software/BeautifulSoup/bs4/doc/index.html>`_ (`MIT License <https://bazaar.launchpad.net/~leonardr/beautifulsoup/bs4/view/head:/LICENSE>`__)
* `lxml <https://github.com/lxml/lxml>`_ (`BSD-3-Clause License <https://github.com/lxml/lxml/blob/master/LICENSE.txt>`__)
* `loguru <https://github.com/Delgan/loguru>`_ (`MIT License <https://github.com/Delgan/loguru/blob/master/LICENSE>`__)
* `single-source <https://github.com/rabbit72/single-source>`_ (`MIT License <https://github.com/rabbit72/single-source/blob/master/LICENSE>`__)

and other amazing Python packages for development and testing.
See a full list of them in 'dependencies' section of ``pyproject.toml``
`file <https://github.com/hotenov/LEP-downloader/blob/main/pyproject.toml>`_.

.. _Luke's ENGLISH Podcast: https://teacherluke.co.uk/archive-of-episodes-1-149/
.. _donating: https://www.paypal.com/donate/?cmd=_s-xclick&hosted_button_id=CA2KNZNBFGKC6
.. _becoming: https://teacherluke.co.uk/premium/premiuminfo/
.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/hotenov/lep-downloader/issues
.. _pip: https://pip.pypa.io/
.. _pipx: https://pipxproject.github.io/pipx/
.. _Releases: https://github.com/hotenov/LEP-downloader/releases

.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://lep-downloader.readthedocs.io/en/latest/usage.html
.. _Manpage: https://lep-downloader.readthedocs.io/en/latest/manpage.html
