#! /usr/bin/env python

import sys
import argparse
from statsnba.resources import StatsNBAPlayByPlay
import pandas as pd

parser = argparse.ArgumentParser(description='Download play-by-play and save in CSV format')

parser.add_argument('--game-id', dest='game_id', help='The game id of the game to download')
parser.add_argument('-o', '--output', dest='output_file', help='The file to write to (default to standard output')

args = parser.parse_args()

pbp = StatsNBAPlayByPlay.fetch_resource({'GameID': args.game_id})

if args.output_file:
    pd.DataFrame(pbp['resultSets']['PlayByPlay']).to_csv(args.output_file)
else:
    sys.stdout.write(pd.DataFrame(pbp['resultSets']['PlayByPlay']).to_csv())


