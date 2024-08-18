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

import re
from dataclasses import dataclass


@dataclass
class Part:
    title: str


@dataclass
class Mission:
    title: str
    id: str
    path: str
    depends_on: list[str]
    tags: list[str]

    def __init__(self, title: str, path: str, depends_on: list[str], tags: list[str]):
        super().__init__()
        self.title = title
        self.path = path
        self.depends_on = depends_on
        self.tags = tags

        self.id = Mission.sanitize_string(self.path)

    @staticmethod
    def sanitize_string(path: str) -> str:
        return re.sub(r'\W+', '', path).lower()
