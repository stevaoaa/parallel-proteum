#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
	This script contanis some methods to handle with files like: testset, functions.. etc.
"""


"""
	Creates a Dictionary with the testcases based in a testset file 
"""
def get_all_test_cases(testset_file):

	"""
	Args:
		testset_file = File that contais the testset used to test the program
	"""

	#One testcase is formed by the inputs.
	testset = {}

	#Defines the number of the testcase
	number_tcase = 1

	for line in testset_file:
		if line != '':
			inputs = line.split()
			testset[number_tcase] = inputs
			number_tcase+=1

	return testset


"""
	Returns a list with all the functions existing in functions.txt file
"""
def get_all_functions(functions_file):

	"""
	Args:
		functions_file = File that list all the existing functions in the program
	"""

	#A empty list
	functions = []

	#Every line in the file is correspondent to a function. So just go through the lines removes the "\ n" and add to the list
	for line in functions_file:
		if line != '':
			functions.append(line.strip(" \n"))

	return functions

"""
	Returns a list with all equivalent mutants
"""
def get_equivalent_mutants(equivalents_file):

	"""
	Args:
		equivalents_file = File that contanis a list with the equivalent mutants
	"""

	#Empty list
	equivalents = []

	for line in equivalents_file:
		if line != '':
			equivalents = equivalents + line.split()

	return equivalents


"""
	Return a string that contains the gcc command used to compile the program
"""
def get_compile_command(compile_file):
	"""
	Args:
		compile_file = File that contanis the gcc command used to compile the program
	"""	

	compile_command = ''

	for line in compile_file:
		if line != '':
			compile_command = compile_command + line

	return compile_command


