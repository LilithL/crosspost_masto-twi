# crosspost_masto-twi
A simple crosspost script that crosspost toots from mastodon to twitter.

## Usage

```main.py print-conf-to-file```: 
Write a default config file to the disk.

```main.py run```: Run the main loop. by default it checks every 20 seconds if new toots were posted and crossposts them to twitter.

```main.py init-db```: Initialise the database

You can use ```--help``` to print the commands and possible options.

## Setup

You must first get your mastodon and twitter api tokens.
For mastodon, you can use the login.py script from [here](https://github.com/LilithL/mastodon-ebooks.py/blob/master/login.py)

For twitter, you must edit the twitter_access_token.secret and twitter_consumer_key.secret accordingly. You can apply for them on the [twitter dev page](https://developer.twitter.com/)