# -*- coding: utf-8 -*-
from os import path
import yaml


__author__ = 'Yicheng Luo'
__email__ = 'ethanluoyc [AT] gmail DOT com'
__version__ = '0.1.0'


config = yaml.safe_load(open(path.join(path.dirname(__file__), '../config.yml'), 'r'))
