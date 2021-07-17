from datetime import datetime, timezone
from time import time
from typing import Optional

from requests import get
import urllib.request
from urllib.error import HTTPError, URLError
from socket import timeout

from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.Storage import ModuleStorage, BASE_PATH

domain = "https://api.github.com"
_logger = Logger("CheckGitUpdater")
_storage = ModuleStorage(BASE_PATH / "Update")
headers = {'User-Agent': 'FFxivPythonTrigger', }


def test_url(url):
    try:
        return urllib.request.urlopen(url, timeout=3).getcode() == 200
    except (HTTPError, URLError) as error:
        _logger.warning('Data of [%s] not retrieved because %s' % (url, error))
    except timeout:
        _logger.warning('socket timed out - URL [%s]' % url)
    return False


def get_last_update(name: Optional[str], current_hash: str, logger: Logger):
    if name is None:
        data_dir =_storage.data.setdefault('core', dict())
    else:
        data_dir = _storage.data.setdefault('plugins', dict()).setdefault(name, dict())
    if 'time' not in data_dir or 'hash' not in data_dir or data_dir['hash'] != current_hash:
        logger.debug("last update time update")
        data_dir['time'] = time()
        data_dir['hash'] = current_hash
    _storage.save()
    return data_dir['time']


def check_update(logger: Logger, repo: str, rpath: str, last_update: float):
    if not can_check:
        logger.warning(f"cant check update of {repo} - {rpath}")

    key = f"{repo} - {rpath}"
    cache = _storage.data.setdefault('cache', dict()).setdefault(key, dict())
    headers_ = headers.copy()
    headers_["If-None-Match"] = cache.setdefault('etag', '')

    try:
        q = get(f"{domain}/repos/{repo}/commits", {'path': rpath, 'page': '1', 'per_page': '1', }, headers=headers_)
    except Exception as e:
        logger.warning(f"cant check update of {repo} - {rpath}: {e}")
    else:
        if q.status_code != 304:
            data = q.json()
            if q.status_code != 200:
                logger.warning(q.json()["message"])
                return
            cache['etag']=q.headers['ETag']
            new_timestamp = datetime.strptime(data[0]["commit"]["author"]["date"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()
            cache['timestamp'] = int(new_timestamp)
            _storage.save()

        t = cache['timestamp']
        if t > last_update:
            logger.warning(f"There is a update at {datetime.fromtimestamp(t)} on https://github.com/{repo}")
        else:
            logger.debug(f"{repo} - {rpath} is up to date")
    _storage.save()


can_check = test_url(domain)
