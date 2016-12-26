#!/usr/bin/envs python

from statsnba import Game
import pandas as pd
import re

import requests_cache
requests_cache.install_cache('test_cache')

game_id = '0020901226'


def process_game_pbp(game_id):
    game = Game(game_id)
    playbyplay = game.PlayByPlay

    def event_to_dict(event):
        # TODO Kind of dirty, so better refactor this
        event_dict = {}
        for field_name in event.Fields:
            field_attr = getattr(event, field_name)
            if field_name == 'EventType':
                event_dict['EventType'] = field_attr.name
            elif field_name in ['Block', 'Assist', 'Steal', 'Home', 'Away', 'Possession', 'Left', 'Entered']:
                event_dict[field_name+'Name'] = getattr(field_attr, 'PlayerName', None)
                event_dict[field_name+'Id'] = getattr(field_attr, 'PlayerId', None)
            elif field_name in ['Team', 'HomeTeam', 'AwayTeam']:
                event_dict[field_name+'Id'] = getattr(field_attr, 'TeamId', None)
                event_dict[field_name+'Abbreviation'] = getattr(field_attr, 'TeamAbbreviation', None)
            elif field_name in ['HomePlayers', 'AwayPlayers']:
                player_lst = sorted(list(field_attr))
                for i in range(5):
                    player_prefix = re.sub('Players$', 'Player{0}'.format(i+1), field_name)
                    event_dict[player_prefix+'_Name'] = player_lst[i].PlayerName
                    event_dict[player_prefix+'_Id'] = player_lst[i].PlayerId
            else:
                event_dict[field_name] = field_attr

        return event_dict

    ev_dict_lst = []
    for ev in playbyplay:
        ev_dict_lst.append(event_to_dict(ev))

    return ev_dict_lst


if __name__ == "__main__":
    df = pd.DataFrame(process_game_pbp(game_id))
    df.to_csv('test.csv')
