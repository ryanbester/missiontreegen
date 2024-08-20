#  Copyright 2024 Ryan Bester
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import urllib
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import requests
from bs4 import BeautifulSoup
from termcolor import colored

from common import Mission, Part
from logger import Logger


class Extractor:
    def get_description(self) -> str:
        pass

    def get_help(self) -> str:
        pass

    def get_parts(self) -> list[Part]:
        pass

    def get_missions(self, part_title) -> list[Mission]:
        pass


class WebExtractor:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_soup(self, path):
        url = urllib.parse.urljoin(self.base_url, path)
        Logger.log_debug(colored(f'Loading URL "{url}"', 'cyan'))

        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html_page = urlopen(req).read()
        except HTTPError as e:
            print(colored(f'Failed to load URL "{url}": {e}', 'red'))
            return None

        return BeautifulSoup(html_page, 'html.parser')

    def find_final_path(self, path) -> str:
        redirect_end = False
        next_loc = urllib.parse.urljoin(self.base_url, path)
        Logger.log_debug(colored(f'Finding redirects for URL "{next_loc}"', 'cyan'))

        while not redirect_end:
            response = requests.get(next_loc, allow_redirects=False)
            if response.status_code in (301, 302):
                location = response.headers['Location']
                next_loc = location
            else:
                redirect_end = True

        # remove fragment from URL
        next_loc = next_loc.split('#')[0]
        Logger.log_debug(colored(f'URL redirects to "{next_loc}"', 'cyan'))
        return next_loc
