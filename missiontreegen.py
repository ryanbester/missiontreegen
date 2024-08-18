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

import argparse
import dataclasses
import json
import os

import bs4
import graphviz.backend
from graphviz import Digraph
from graphviz2drawio import graphviz2drawio
from tabulate import tabulate
from termcolor import colored

from extractors import *
from logger import Logger

os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'

EXTRACTORS = {
    'rdr': rdr.Rdr
}


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def main():
    if os.name == 'nt':
        os.system('color')

    parser = argparse.ArgumentParser(prog='missiontreegen', description="Mission tree generator")
    # 0 - INFO
    # 1 - VERBOSE
    # 2 - DEBUG
    # 3 - TRACE
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='enable verbose logging (repeat to increase level of verbosity)')

    subparsers = parser.add_subparsers(dest='command', required=True)

    info_parser = subparsers.add_parser('info', help='show information about %(prog)s')
    info_parser.add_argument('extractor', nargs='?', help='the extractor')
    info_parser.set_defaults(func=info)

    extract_parser = subparsers.add_parser('extract', help='extract data')
    extract_parser.add_argument('--extractor', required=True, help='the extractor to use')
    extract_parser.add_argument('--output-file', required=True, help='output file for the extracted data')
    extract_parser.set_defaults(func=extract)

    generate_tree_parser = subparsers.add_parser('generate-tree', help='generate a tree')
    generate_tree_parser.add_argument('--input-file', required=True, help='input file to generate the tree from')
    generate_tree_parser.add_argument('--output-file', required=True, help='output file for the generated tree')
    generate_tree_parser.add_argument("--part", required=False, help='the part to generate the tree for')
    generate_tree_parser.add_argument('--subgraphs', required=False, default=False, help='draw borders around each part')
    generate_tree_parser.add_argument('--style', required=False, help='the style file')
    generate_tree_parser.add_argument('--format', required=True, help='the format of the tree')
    generate_tree_parser.set_defaults(func=generate_tree)

    args = parser.parse_args()
    Logger.set_level(args.verbose)

    args.func(args)


def format_tabulate_line(table, line_fmt):
    return '\n'.join(line_fmt.format(line=line) for line in table.split('\n'))


def info(args):
    if args.extractor:
        if args.extractor in EXTRACTORS:
            extractor = EXTRACTORS[args.extractor]
        else:
            print('No extractor found with that name')
            return

        print(f'Information for {args.extractor}:')
        inst = extractor()
        extractor_table = [
            ['Name', args.extractor],
            ['Class', inst.__class__.__name__],
            ['Description', inst.get_description()],
        ]
        print(tabulate(extractor_table, tablefmt='plain'))
        print('\n' + inst.get_help())
        return

    print(f'BeautifulSoup Version: {bs4.__version__}')

    print('Graphviz Information:')
    graphviz_table = [
        ['Version', graphviz.version()],
        ['Dot Binary', graphviz.DOT_BINARY],
        ['Unflatten Binary', graphviz.UNFLATTEN_BINARY],
        ['Renderers', ' '.join(graphviz.RENDERERS)],
        ['Engines', ' '.join(graphviz.ENGINES)],
        ['Formats', ' '.join(graphviz.FORMATS)],
        ['Formatters', ' '.join(graphviz.FORMATTERS)],
    ]
    print(format_tabulate_line(
        tabulate(graphviz_table, tablefmt='plain', maxcolwidths=[None, os.get_terminal_size().columns - 32]),
        '\t{line}'))

    print('Extractors:')
    extractors_table = []
    for extractor in list(EXTRACTORS):
        extractors_table.append([extractor, EXTRACTORS[extractor]().get_description()])

    headers = ["NAME", "DESCRIPTION"]
    print(format_tabulate_line(tabulate(extractors_table, headers, tablefmt='plain'), '\t{line}'))


def extract(args):
    Logger.log_info(f"Extracting data of type: {args.extractor}")
    Logger.log_info(f"Output will be saved to: {args.output_file}")

    extractor = EXTRACTORS[args.extractor]()

    Logger.log_info("Getting parts")
    parts = extractor.get_parts()
    if parts is None:
        return

    data = {'parts': []}

    for part in parts:
        Logger.log_info(colored(f"Getting missions for part {part.title}", "light_grey"))
        missions = extractor.get_missions(part.title)
        data['parts'].append({'title': part.title, 'missions': missions})

    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, cls=EnhancedJSONEncoder)


def generate_tree(args):
    Logger.log_info(f"Generating tree from: {args.input_file}")
    Logger.log_info(f"Output will be saved to: {args.output_file}")

    with open(args.input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if args.style is not None:
        with open(args.style, 'r', encoding='utf-8') as f:
            style = json.load(f)

    fmt = args.format
    if args.format == 'drawio':
        fmt = 'png'

    dot = Digraph(comment='Mission Dependency Graph', format=fmt, engine='dot')
    dot.attr(overlap='false')
    dot.attr(sep='0.5')
    dot.attr(splines='true')
    dot.attr(rankdir='TB')

    for part in data['parts']:
        if args.subgraphs:
            with dot.subgraph(name=f'cluster_{part['title'].replace(" ", "_")}') as c:
                c.attr(label=part['title'], color='blue', style='dashed')
                for mission in part['missions']:
                    c.node(mission['id'], mission['title'])

                    for dependency in mission['depends_on']:
                        c.edge(dependency, mission['id'])
        else:
            for mission in part['missions']:
                # dot.node(mission['id'], mission['title'], image='image.png', shape='rectangle')

                if style is not None:
                    node_style = None
                    for tag in mission['tags']:
                        if tag in style:
                            node_style = style[tag]
                    if node_style is None:
                        node_style = style['default']
                    dot.node(mission['id'], mission['title'], shape='rectangle', style='filled',
                             fillcolor=node_style['background_color'])
                else:
                    dot.node(mission['id'], mission['title'], shape='rectangle')

                for dependency in mission['depends_on']:
                    dot.edge(dependency, mission['id'])

    if args.format != 'drawio':
        render_name = dot.render(f'{args.output_file}', view=True)
        Logger.log_info(f'Graph saved as {render_name}')
    else:
        output_name = dot.save(f'{args.output_file}' + '.dot')
        xml = graphviz2drawio.convert(output_name)
        with open(args.output_file, 'w', encoding='utf-8') as f2:
            f2.write(xml)


if __name__ == '__main__':
    main()
