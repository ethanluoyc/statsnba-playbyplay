===================
statsnba-playbyplay
===================

.. image:: https://img.shields.io/pypi/v/statsnba-playbyplay.svg?maxAge=2592000
   :target: https://pypi.python.org/pypi?name=statsnba-playbyplay&version=0.1.0&:action=display
   :alt: PyPi Version

.. image:: https://readthedocs.org/projects/statsnba-playbyplay/badge/?version=latest
   :target: http://statsnba-playbyplay.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

NOTE: This project is still pretty much work in progress so it might
introduce many breaking changes.

- `Introduction`_
- `Use the data`_
- `Benefits of this package`_
- `Installation`_
- `TODOs`_

Introduction
------------

Basketball analytics using play-by-play data have been an shared
interest for many people. However, the lack of processed play-by-play
has prohibited such analysis by many.

This project is intended to provide parsing functionality for the
play-by-play data from http://stats.nba.com into more a comprehensive
format like that on
`NBAStuffer <https://downloads.nbastuffer.com/nba-play-by-play-data-sets>`__.
It is intended to accompany our research: `Adversarial Synergy Graph
Model for Predicting Game Outcomes in Human
Basketball <http://www.somchaya.org/papers/2015_ALA_Liemhetcharat.pdf>`__.
to prepare the data. If you are interested in more general statistics or
player information, you should definitely check out
`py-Goldsberry <https://github.com/bradleyfay/py-Goldsberry>`__.

While there are still limitations with the current parsing strategy, it
does not affect the tabulation of APM and other play-by-play based
metrics.

Use the data
------------

If you just want to use the data that is processed with the package
without touching it, you can find a copy of the data
`from S3 <http://statsnba.s3-website-us-east-1.amazonaws.com/>`__. Under
``data/zip/`` you will find the gamelog and game files in JSON format.
You may introspect into the JSONs for the fields that are included in
them.

Benefits of this package
------------------------

-  The data is obtained directly from http://stats.nba.com, the parsed
   play-by-plays can be verified against the official boxscores.


Installation
------------

At the command line

  .. code:: shell                
            
    $ pip install statsnba-playbyplay


TODOs
-----

-  Documentation.
-  Parse subtypes of events. (e.g. when there is a shot, is it a layup
   or jumpshot? the raw data provides different codes for these subtypes
   but I have not yet figured out a way to easily decrypt all of them.)
-  More tests at all levels of the package.
-  A Github Pages website for showcasing the package.
-  Wiki pages on the schema of the parsed data on my S3 bucket.
-  Daily updates of the data feed (cronjob or Lambda function on an EC2
   instance to track the gamelogs daily and make updates on S3?)
