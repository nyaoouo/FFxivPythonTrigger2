import urllib.request
from urllib.error import HTTPError, URLError
from pkg_resources import DistributionNotFound, VersionConflict, require
from urllib.parse import urlsplit
import socket
import pip

pip_source_name = "default"
pip_source = "https://pypi.python.org/simple"
pip_sources = {
    '阿里云': 'http://mirrors.aliyun.com/pypi/simple/',
    '豆瓣(douban)': 'http://pypi.douban.com/simple/',
    '清华大学': 'https://pypi.tuna.tsinghua.edu.cn/simple',
}


def test_url(url):
    try:
        code = urllib.request.urlopen(url, timeout=5).getcode()
        return code == 200, code
    except (HTTPError, URLError, socket.timeout) as error:
        return False, error


back = list(pip_sources.items())
while not test_url(pip_source):
    if not back:
        pip_source_name = pip_source = None
        break
    pip_source_name, pip_source = back.pop(0)


def test_requirements(arg):
    try:
        require(arg)
    except DistributionNotFound:
        return False
    except VersionConflict:
        return False
    else:
        return True


def install(*pkgs):
    if pip_source is None:
        raise Exception("No valid source for pip")
    param = ['install', *pkgs, '-i', pip_source, '--trusted-host', urlsplit(pip_source).netloc]
    if hasattr(pip, 'main'):
        pip.main(param)
    else:
        pip._internal.main(param)
