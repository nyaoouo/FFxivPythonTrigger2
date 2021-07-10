from datetime import datetime, timezone

from requests import get
import urllib.request
from urllib.error import HTTPError, URLError
from socket import timeout

from FFxivPythonTrigger.Logger import Logger

domain = "https://api.github.com"

_logger = Logger("CheckGitUpdater")

EMPTY = datetime.fromtimestamp(0.)

headers = {
    'User-Agent': 'FFxivPythonTrigger',
}


def test_url(url):
    try:
        return urllib.request.urlopen(url, timeout=3).getcode() == 200
    except (HTTPError, URLError) as error:
        _logger.warning('Data of [%s] not retrieved because %s' % (url, error))
    except timeout:
        _logger.warning('socket timed out - URL [%s]' % url)
    return False


def get_last_commit_time(repo: str, path: str):
    if not can_check: return EMPTY
    q = get(f"{domain}/repos/{repo}/commits", {'path': path, 'page': '1', 'per_page': '1', }, headers=headers)
    if q.status_code != 200: raise Exception(q.json()["message"])
    return datetime.strptime(q.json()[0]["commit"]["author"]["date"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


can_check = test_url(domain)
