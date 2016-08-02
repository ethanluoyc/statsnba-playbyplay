#!/usr/bin/env python

# example: 0020901003

from statsnba.api import Api
import pandas as pd

import argparse
parser = argparse.ArgumentParser(description='Download Pbp')

parser.add_argument('-i', '--id', required=True,
                    dest='game_id', help='game_id to download')

parser.add_argument('-o', '--output', required=True,
                    dest='output', help='file to save')

parser.add_argument('-f', '--format', dest='format',
                    default='excel', choices={'csv', 'excel'}, action='store')

if __name__ == '__main__':
    args = parser.parse_args()
    game_id = args.game_id
    print 'Downloading game {0}'.format(game_id)
    api = Api()
    result = api.GetPlayByPlay(game_id)
    df = pd.DataFrame(result['resultSets']['PlayByPlay'])
    print 'Saving to {0}'.format(args.output)
    if args.format == 'csv':
        df.to_csv(args.output)
    else:
        df.to_excel(args.output)
