import configparser
import json
import time

import click
import twitter

import Masto_crosspost_utils
import models_db

# The global var that'll contain the parameters from the config file
PARAMS = {}


@click.group()
def cli():
    pass


def read_conf(conf_file):
    global PARAMS
    try:
        configParser = configparser.RawConfigParser()
        configParser.read(conf_file)
    except Exception as e:
        print(e)
        exit(1)
    PARAMS = configParser._sections['config-crosspost']


def import_json_file(file_name):
    """ Read a json file then decodes it to a dict
    """
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except:
        print("No "+file_name+" file found")
        exit()


def tweet_parser(twi_api, texte, toot_cont_warn, last_tweet_id=None, toot_media=None):
    """ Construct tweets based on a toot content and cw and tweet it
    """
    if toot_cont_warn != "":
        formated_cw = PARAMS['twi_cw_default'].replace(
            "\\n", "\n").format(toot_cont_warn)
    else:
        formated_cw = ""

    if not any(word in toot_cont_warn.lower() for word in PARAMS['no_cp_indicators'].split(',')):
        texte = Masto_crosspost_utils.process_toot_to_chunks(
            texte, int(PARAMS['twi_limit']) - len(formated_cw))
        for contenu in texte:
            try:
                last_tweet_id = twi_api.PostUpdate(status=formated_cw + contenu, in_reply_to_status_id=last_tweet_id,
                                                   verify_status_length=False, media=toot_media).id
            except Exception as e:
                print("Erreur, prochain essais dans 3 secondes : ", e)
                time.sleep(3)
                try:
                    last_tweet_id = twi_api.PostUpdate(status=formated_cw + contenu, in_reply_to_status_id=last_tweet_id,
                                                       verify_status_length=False, media=toot_media).id
                except Exception as e:
                    print("Erreur, pas de nouvelles tentatives: ", e)
                    return
    return last_tweet_id


def tweet_last_toots(mastodon_utils, twi_api, acct):
    """ Get the last toots from a given account id and post it on twitter
    """
    # Access the database, if it fails stop the program
    try:
        database = models_db.Session_db(PARAMS['db_file'])
        if len(mastodon_utils.scrape_toots(acct.id, None)) < 1:
            return
    except Exception as e:
        print(e)
        exit()

    # Get last toot from database, if it fails create a crossposted_toots object with default values
    l_toot = database.get_last_toot(acct.id)
    if l_toot == None:
        database.add_toot(acct['id'], mastodon_utils.scrape_toots(acct.id, None)[-1]['id'], None)
        l_toot = database.get_last_toot(acct.id)

    # Get the last toots on the target account since the last toot id given in l_toot
    last_toots = mastodon_utils.scrape_toots(
        acct.id, l_toot.toot_id)

    if len(last_toots) > 0:
        for new_toot in last_toots:
            new_toot_media = []

            # Get the tweet id to answer to
            tweet_id = database.get_tweet_id(new_toot['in_reply_to_id'])

            # Get the medias in the toot
            for media in new_toot['media_attachments']:
                new_toot_media.append(media['url'])

            tweet_id = tweet_parser(twi_api, new_toot['content'],
                                    new_toot['spoiler_text'],  tweet_id, new_toot_media)
            database.add_toot(acct['id'], new_toot['id'], tweet_id)
    return


@cli.command()
@click.option('-c', '--conf', type=click.Path(), default='param.conf', help='The path to the configuration file')
@click.option('-d', '--delay', default=20, help='The time delay before checking again the accounts for new toots')
def run(conf, delay):
    """ Run the crosspost bot main loop 
    """
    read_conf(conf)
    usercred_masto = import_json_file(PARAMS['masto_usercred_file'])
    mastodon_utils = Masto_crosspost_utils.MastoCrosspostUtils(
        PARAMS['masto_clientcred_file'], usercred_masto['token'], usercred_masto['url'])

    accesstoken_twitter = import_json_file(PARAMS['twi_accesstoken_file'])
    consumerkey_twitter = import_json_file(PARAMS['twi_consumerkey_file'])
    twi_api = twitter.Api(
        consumer_key=consumerkey_twitter['key'],
        consumer_secret=consumerkey_twitter['secret'],
        access_token_key=accesstoken_twitter['key'],
        access_token_secret=accesstoken_twitter['secret']
    )

    while 1:
        if PARAMS['is_external_acct'].lower() == 'true':
            for mstdn_acct in mastodon_utils.get_following():
                tweet_last_toots(mastodon_utils, twi_api, mstdn_acct)
        elif PARAMS['is_external_acct'].lower() == 'false':
            tweet_last_toots(mastodon_utils, twi_api, mastodon_utils.me)
        else:
            raise Exception(
                "Parameter 'is_external_acct' is undefined in config file")
        time.sleep(20)


@cli.command()
@click.option('-o', '--output', type=click.Path(), default='param.conf', help='The path to the configuration file to write in')
def print_conf_to_file(output):
    """ Write a default config file
    """
    try:
        with open(output, 'w') as f:
            f.write("[config-crosspost]\n\n" +
                    "# The twitter's tweet size limit\n" +
                    "twi_limit = 280\n\n" +
                    "# List of no-crosspost identificator (use \",\" as a delimiter)\n" +
                    "no_cp_indicators =nocp,lb,~\n\n" +
                    "# Twitter cw formating\n" +
                    "twi_cw_default = [{}]\\n\\n \n\n" +
                    "# The file that will contain the info about the last toot processed by the crossposter\n" +
                    "last_toot_file = lastToot.json\n\n" +
                    "# Tells wether to crosspost the following accounts (true) or itself (false)\n" +
                    "is_external_acct = True\n\n" +
                    "# The path to the twitter api tokens\n" +
                    "twi_accesstoken_file = twitter_access_token.secret\n" +
                    "twi_consumerkey_file = twitter_consumer_key.secret\n\n" +
                    "# The path to the mastodon api tokens\n" +
                    "masto_clientcred_file = clientcred.secret\n" +
                    "masto_usercred_file = usercred.secret\n\n" +
                    "# The sqlite3 file name\n" +
                    "db_file = toots.sqlite3")
    except Exception as e:
        print(e)
        exit(1)


@cli.command()
@click.option('-c', '--conf', type=click.Path(), default='param.conf', help='The path to the configuration file')
def init_db(conf):
    read_conf(conf)
    models_db.init(PARAMS['db_file'])


if __name__ == "__main__":
    cli()
