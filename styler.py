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

import json

from logger import Logger


class Styler:
    @classmethod
    def load_style(cls, style_path):
        if style_path is None:
            cls.style_engine = None
            return

        with open(style_path, 'r', encoding='utf-8') as f:
            cls.style = json.load(f)

        cls.style_engine = 'gv'
        if 'engine' in cls.style:
            cls.style_engine = cls.style['engine']
            if cls.style_engine != 'gv' and cls.style_engine != 'html':
                print('Invalid style engine, must be gv or html')
                return

    @classmethod
    def get_style(cls, node_id, tags):
        if cls.style is None:
            return None

        matching_styles = []

        for selector, selector_style in cls.style.items():
            if selector == 'engine':
                continue

            Logger.log_trace(f'Selector: {selector} for tags {tags}, id {node_id}')
            if selector in tags or selector == '#' + node_id:
                if 'inherit' in selector_style:
                    if selector_style['inherit'] in cls.style:
                        matching_styles.append(cls.style[selector_style['inherit']] | selector_style)
                        continue
                matching_styles.append(selector_style)

        if len(matching_styles) < 1:
            if 'default' not in cls.style:
                return None
            node_style = cls.style['default']
        else:
            node_style = {k: v for style in matching_styles for k, v in style.items()}

        return node_style

    @classmethod
    def set_attr_if_exists(cls, node_style, attrs, style_name, attr_name, validator=None):
        if style_name in node_style:
            if validator is not None:
                value = validator(node_style[style_name])
                if value is not None:
                    attrs[attr_name] = value
            else:
                attrs[attr_name] = node_style[style_name]

    @classmethod
    def make_html_kwargs(cls, node_style):
        attrs = {}

        cls.set_attr_if_exists(node_style, attrs, 'line_color', 'color')
        cls.set_attr_if_exists(node_style, attrs, 'background_color', 'fillcolor')
        cls.set_attr_if_exists(node_style, attrs, 'comment', 'comment')
        cls.set_attr_if_exists(node_style, attrs, 'href', 'href')
        cls.set_attr_if_exists(node_style, attrs, 'orientation', 'orientation')
        cls.set_attr_if_exists(node_style, attrs, 'pen_width', 'penwidth')
        cls.set_attr_if_exists(node_style, attrs, 'shape', 'shape')
        cls.set_attr_if_exists(node_style, attrs, 'polygon_sides', 'sides')
        cls.set_attr_if_exists(node_style, attrs, 'polygon_skew', 'skew')
        cls.set_attr_if_exists(node_style, attrs, 'style', 'style')

        return attrs

    @classmethod
    def make_kwargs(cls, node_style):
        attrs = cls.make_html_kwargs(node_style)

        cls.set_attr_if_exists(node_style, attrs, 'polygon_distortion', 'distortion')
        cls.set_attr_if_exists(node_style, attrs, 'font_color', 'fontcolor')
        cls.set_attr_if_exists(node_style, attrs, 'font', 'fontname')
        cls.set_attr_if_exists(node_style, attrs, 'font_size', 'fontsize')
        cls.set_attr_if_exists(node_style, attrs, 'image', 'image', lambda value: 'images/' + value)
        cls.set_attr_if_exists(node_style, attrs, 'image_pos', 'imagepos',
                               lambda value: value if value in ['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc',
                                                                'br'] else None)
        cls.set_attr_if_exists(node_style, attrs, 'image_scale', 'imagescale')
        cls.set_attr_if_exists(node_style, attrs, 'margin', 'margin')

        return attrs

    @classmethod
    def make_html(cls, node_style, title):
        image_html = ''
        image_width = ''
        image_height = ''
        if 'image_width' in node_style:
            image_width = f'WIDTH="{node_style['image_width']}"'
        if 'image_height' in node_style:
            image_height = f'height="{node_style['image_height']}"'
        if 'image' in node_style:
            image_html = f'<TD FIXEDSIZE="TRUE" {image_width} {image_height}><IMG SRC="{'images/' + node_style['image']}"/></TD>'

        html = f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0"><TR>'

        image_pos = 'ml'
        if 'image_pos' in node_style:
            image_pos = node_style['image_pos']

        if image_pos in ['tl', 'ml', 'bl']:
            html += image_html

        font_color = ''
        if 'font_color' in node_style:
            font_color = f'COLOR="{node_style['font_color']}"'

        font_size = ''
        if 'font_size' in node_style:
            font_size = f'POINT-SIZE="{node_style['font_size']}"'

        font = ''
        if 'font' in node_style:
            font = f'FACE="{node_style['font']}"'

        html += f'<TD><FONT {font_color} {font_size} {font}>' + title + '</FONT></TD>'

        if image_pos in ['tr', 'mr', 'br']:
            html += image_html

        html += '</TR></TABLE>'

        Logger.log_trace(f'Generated HTML = {html}')

        return f'<{html}>'

    @classmethod
    def make_node(cls, graph, node_id, title, tags):
        node_style = cls.get_style(node_id, tags)
        if node_style is None:
            graph.node(node_id, title)
            return

        if cls.style_engine == 'gv':
            graph.node(node_id, title, **cls.make_kwargs(node_style))
        elif cls.style_engine == 'html':
            graph.node(node_id, cls.make_html(node_style, title), **cls.make_html_kwargs(node_style), margin='0')
        else:
            graph.node(node_id, title)
