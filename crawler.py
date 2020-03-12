# -*- coding: utf-8 -*-
"""
Crawler application
"""
import logging
import re
from abc import abstractmethod
from concurrent import futures
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment

import cfscrape

logger = logging.getLogger(__name__)


class Crawler:
    '''Blueprint for creating new crawlers'''

    def __init__(self):
        self.executor = futures.ThreadPoolExecutor(max_workers=2)
        self.scrapper = cfscrape.create_scraper()
        self.scrapper.verify = False

        self._destroyed = False
    # end def

    def destroy(self):
        self._destroyed = True
        self.scrapper.close()
        self.executor.shutdown(False)
    # end def

    # ------------------------------------------------------------------------- #
    # Implement these methods
    # ------------------------------------------------------------------------- #

    @abstractmethod
    def initialize(self):
        pass
    # end def

    # ------------------------------------------------------------------------- #
    # Helper methods to be used
    # ------------------------------------------------------------------------- #
    @property
    def headers(self):
        return self.scrapper.headers.copy()
    # end def

    @property
    def cookies(self):
        return {x.name: x.value for x in self.scrapper.cookies}
    # end def

    def absolute_url(self, url, page_url=None):
        url = (url or '').strip()
        if not page_url:
            page_url = self.last_visited_url
        # end if
        if not url or len(url) == 0:
            return None
        elif url.startswith('//'):
            return self.home_url.split(':')[0] + ':' + url
        elif url.find('//') >= 0:
            return url
        elif url.startswith('/'):
            return self.home_url + url
        elif page_url:
            page_url = page_url.strip('/')
            return (page_url or self.home_url) + '/' + url
        else:
            return url
        # end if
    # end def

    def is_relative_url(self, url):
        page = urlparse(self.novel_url)
        url = urlparse(url)
        return (page.hostname == url.hostname
                and url.path.startswith(page.path))
    # end def

    def get_response(self, url, **kargs):
        if self._destroyed:
            return None
        # end if
        kargs = kargs or dict()
        kargs['verify'] = kargs.get('verify', False)
        kargs['timeout'] = kargs.get('timeout', 150)  # in seconds
        self.last_visited_url = url.strip('/')
        response = self.scrapper.get(url, **kargs)
        response.encoding = 'utf-8'
        self.cookies.update({
            x.name: x.value
            for x in response.cookies
        })
        response.raise_for_status()
        return response
    # end def

    def submit_form(self, url, data={}, multipart=False, headers={}):
        '''Submit a form using post request'''
        if self._destroyed:
            return None
        # end if

        headers.update({
            'Content-Type': 'multipart/form-data' if multipart
            else 'application/x-www-form-urlencoded; charset=UTF-8',
        })

        response = self.scrapper.post(url, data=data, headers=headers)
        response.encoding = 'utf-8'
        self.cookies.update({
            x.name: x.value
            for x in response.cookies
        })
        response.raise_for_status()
        return response
    # end def

    def get_soup(self, *args, parser='lxml', **kargs):
        response = self.get_response(*args, **kargs)
        html = response.content.decode('utf-8', 'ignore')
        soup = BeautifulSoup(html, parser)
        if not soup.find('body'):
            raise ConnectionError('HTML document was not loaded properly')
        # end if
        return soup
    # end def

    def get_json(self, *args, **kargs):
        response = self.get_response(*args, **kargs)
        return response.json()
    # end def

    def download_cover(self, output_file):
        response = self.get_response(self.novel_cover)
        with open(output_file, 'wb') as f:
            f.write(response.content)
        # end with
    # end def

# end class
