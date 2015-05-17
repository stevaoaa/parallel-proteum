#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import zlib


"""
	This file define some methods to serialize and deserialize data
"""


"Compress data"
def compress(data):
	data = json.dumps(data)
	data = zlib.compress(data) 
	return data

"Decompress data"
def decompress(data):
	data = zlib.decompress(data)
	data = json.loads(data)
	return data
