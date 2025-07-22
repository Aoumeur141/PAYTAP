#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
config.py : Utility functions to read and load configuration files in Json format 
"""
import json 

def load_config(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found. Make sure {file} exists.")
        exit(1)
