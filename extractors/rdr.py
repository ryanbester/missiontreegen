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

from termcolor import colored

from common import Mission, Part
from extractor import Extractor, WebExtractor
from logger import Logger


class Rdr(Extractor):
    def __init__(self):
        self.missions = None
        self.web_extractor = WebExtractor('https://reddead.fandom.com')

    def get_description(self) -> str:
        return 'Red Dead Redemption'

    def get_help(self) -> str:
        return 'Long help message'

    def get_parts(self) -> list[Part] | None:
        soup = self.web_extractor.get_soup('/wiki/Missions_in_Redemption')
        if soup is None:
            return None

        h2 = soup.select_one('h2 #Single_Player').find_parent('h2')
        Logger.log_trace(f'h2 = {h2}')
        parts = []
        missions = {}

        for sibling in h2.find_next_siblings():
            Logger.log_trace(f'sibling = {sibling}')
            if sibling.name == 'h2':
                Logger.log_trace('Found another h2, exiting loop')
                break

            if sibling.name == 'h3':
                part_name = sibling.find_next('span').text
                Logger.log_trace(f'Found part "{part_name}"')
                missions[part_name] = []
                parts.append(Part(part_name))
            else:
                if len(list(missions)) < 1:
                    continue
                Logger.log_trace(f'Appending "{sibling} to list "{list(missions)[-1]}"')
                missions[list(missions)[-1]].append(sibling)

        self.missions = missions
        return parts

    def get_missions(self, part_title) -> list[Mission]:
        missions = self.missions[part_title]
        missions_obj = []
        for mission in missions:
            for li in mission.find_all('li'):
                mission_name = li.select_one('a')['title']
                Logger.log_trace(f'li = {li}')
                Logger.log_trace(f'Found mission "{mission_name}"')

                mission_path = li.select_one('a')['href']
                mission_path = self.web_extractor.find_final_path(mission_path)

                mission_soup = self.web_extractor.get_soup(mission_path)

                tags = []
                giver = self.get_mission_given_by(mission_soup)
                if giver is not None:
                    tags.append(f'giver.{giver}')
                location = self.get_mission_location(mission_soup)
                if location is not None:
                    tags.append(f'location.{location}')

                depends = self.get_depends(mission_soup)
                if len(depends) < 1:
                    Logger.log_info("Mission {} {}".format(mission_name, colored('has no dependencies', 'red')))
                else:
                    Logger.log_verbose(
                        "Mission {} {}".format(mission_name, colored(f'has {len(depends)} dependencies:', 'green')))
                    for depend in depends:
                        Logger.log_debug("\t{}".format(depend))
                missions_obj.append(Mission(mission_name, mission_path, depends, tags))

        return missions_obj

    def get_mission_given_by(self, soup):
        giver = soup.find('div', {'data-source': 'giver'})
        Logger.log_trace(f'giver = {giver}')
        if giver is not None:
            giver_name = giver.find('a').text
            Logger.log_trace(f'giver_name = {giver_name}')
            return Mission.sanitize_string(giver_name)
        return None

    def get_mission_location(self, soup):
        location = soup.find('div', {'data-source': 'location'})
        Logger.log_trace(f'location = {location}')
        if location is not None:
            a = location.find('a')
            if a is not None:
                location_name = a.text
                Logger.log_trace(f'location_name = {location_name}')
                return Mission.sanitize_string(location_name)
        return None

    def get_depends(self, soup):
        h3 = soup.select_one('h3 #Mission_Prerequisites')
        Logger.log_trace(f'h3 = {h3}')

        if h3 is None:
            return []

        depends = []

        ul = None
        p = None
        for sibling in h3.find_parent('h3').find_next_siblings():
            if sibling.name == 'h3':
                Logger.log_trace('Found another h3, exiting loop')
                break

            if sibling.name == 'ul':
                Logger.log_trace(f'ul = {sibling}')
                ul = sibling

            if sibling.name == 'p':
                Logger.log_trace(f'p = {sibling}')
                p = sibling

        if ul is None and p is not None:
            # Check for note saying the mission starts automatically
            if 'automatically' in p.text or 'following' in p.text:
                a = p.find_next('a')
                Logger.log_trace(f'a = {a}')
                if a is not None:
                    path = a['href']
                    path = self.web_extractor.find_final_path(path)
                    return [Mission.sanitize_string(path)]
            return []

        for li in ul.select('li'):
            if li.name != 'li':
                continue

            links = li.select('a')
            Logger.log_trace(f'links = {links}')
            if len(links) > 0:
                path = links[-1]['href']
                path = self.web_extractor.find_final_path(path)
                depends.append(Mission.sanitize_string(path))

        return depends
