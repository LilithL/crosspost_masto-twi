from bs4 import BeautifulSoup
from mastodon import Mastodon
import html
from urllib.parse import urlparse


class MastoCrosspostUtils:

    def __init__(self, clientcred_key, access_token_key, instance_url):
        self.mastodon_api = Mastodon(
            client_id=clientcred_key,
            access_token=access_token_key,
            api_base_url=instance_url
        )
        self.me = self.mastodon_api.account_verify_credentials()

    def scrape_toots(self, mstdn_acct_id, since=None):
        """ Get toots from an account since given toot id and filter them
        """
        toots = self.mastodon_api.account_statuses(
            mstdn_acct_id, since_id=since, exclude_replies=True)
        filtered_toots = []
        if len(toots):
            filtered_toots = list(filter(lambda x:
                                         x['reblog'] is None and
                                         x['poll'] is None and
                                         x['visibility'] in [
                                             "public", "unlisted", "private"],
                                         toots[::-1]))
        return filtered_toots

    def get_following(self):
        return self.mastodon_api.account_following(self.me.id)


def process_toot_to_chunks(toot_content, size):
    return str_to_chunks(strip_tags(toot_content), size)


def strip_tags(content):
    """ Strip html tags from a given text (ere, we use it to strip tags from toots)
    """
    soup = BeautifulSoup(content, 'html.parser')

    # Removes cards
    tags = soup.select('.h-card')
    for i in tags:
        i.replace_with(i.next_element)

    # Transforms # to text
    tags = soup.select('.hashtag')
    for i in tags:
        i.replace_with(i.get_text())

    # transform mentions text like "user@example.com"
    tags = soup.select('.mention')
    for i in tags:
        mention_acct_url = urlparse(i["href"])
        i.replace_with(
            mention_acct_url.path[2:] + "@" + mention_acct_url.netloc)

    # clear shortened link captions
    tags = soup.select('.invisible, .ellipsis')
    for i in tags:
        i.unwrap()

    # replace link text to avoid caption breaking
    tags = soup.select('a')
    for i in tags:
        i.replace_with(i.get_text())

    # replace emojis with their utf-8 equivalent or text for custom ones
    tags = soup.select('.emojione')
    for i in tags:
        i.replace_with(i['alt'])

    # Replace line break with \n
    line_break = soup.find_all('br')
    for i in line_break:
        i.replace_with('\n ')

    # Replace p with \n\n
    line_break = soup.find_all('p')
    if len(line_break) > 1:
        for i in line_break[1:]:
            i.replace_with('\n\n '+i.get_text())

    # strip html tags, chr(31) joins text in different html tags
    return soup.get_text()


def str_to_chunks(string, size):
    """ Construct a list of strings with a given max size for each strings.
    """
    res = [""]
    words = string.split(' ')
    i = 0
    while len(words):
        if len(res[i]) + len(words[0]) < size:
            res[i] = res[i] + " " + words[0]
            words = words[1:]
        else:
            i += 1
            if len(words[0]) >= size:
                res.append(words[0][:size - 1] + "-")
                words[0] = words[0][size - 1:]
            else:
                res.append("")

    return res
