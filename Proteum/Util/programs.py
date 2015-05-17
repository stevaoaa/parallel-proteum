#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import listdir
from os.path import isfile, isdir


"""
	This method list all the programs in one directory and creates a list with the name of the programs.
	It's userfull to run all the programs in one execution
"""
def list_programs():

	programs = listdir(".")
	list_of_programs = []

	for program in programs:
	
		if (not isdir(program)):
			continue
		list_of_programs.append(program)

	return list_of_programs
