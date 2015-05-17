#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import types
import logging
import subprocess

from Proteum.Util import mutant_util
from Proteum.Util import constants

"""
	Class that implementes a  interface for the execution of the Proteum modules.
"""

verbose = True

class Proteum():

	program = None
	testset = None
	session = None
	verbose = True

	"""
	Constructor
	"""
	def __init__(self,program,session, verbose=True):
		
		"""
		Args:
			program = Program name
			testset = file contains the suite of testcases
			session = name of the session of test
		"""
		
		self.program = program
		self.session = session
		self.verbose = verbose



	"""
	Creates a new test session. It means, it creates all the files necessary
	to run a test on a C program.

	The research mode is enable default, if you want test mode, set research = False
	on the method call    
	"""
	def test_new(self,compile_command, research = True):
		
		"""
		Args:
		      compile_command -  specifies the command used to compile the program using GCC.
		      research - If True, start the Proteum execution in research mode (default is True).
		"""

		if research:
			statment1 = 'test-new -research -C "%s" ' % (compile_command) + self.program
		else:
			statment1 = 'test-new -test ' + self.program

		statment  = compile_command 
		statment2 = 'instrum -EE ' + self.program + ' __' + self.program
		statment3 = 'instrum -build ' + ' __' + self.program + ' ' + self.program

		os.system(statment)  #Compile the program
		os.system(statment1) #Create the test session
		os.system(statment2) #Instrum
		os.system(statment3) #Build

		if verbose: print 'Proteum: A new test session was created'



	"""
	This method is used to add some test cases in a Proteum test session.
	"""
	def tcase_add(self, testcase_list):
		
		"""
		Args:
			testcase_list = a list witch contains the inputs of the test cases that want to add
				if testcase_list is a empty list, them will insert a test case with no parameters
		"""

		test_case = mutant_util.list_string(testcase_list) #Convert testcase_list in a suitable string to use in Proteum

		if not testcase_list:
			statment = 'tcase-add -timeout 300 -trace ' + self.session
		else:
			statment = 'tcase-add -timeout 300 -trace -p %s ' % (test_case) + self.session 

		#if verbose: print '\nProteum: ' + statment #Dont need print because Proteum already make a print on stdout when add a new TC
		if verbose: print "Proteum: Adding a new  test case for the program under test! Test Case: %s " % (test_case)
		os.system(statment)
		print '\n' #put a \n because at the end of execution proteum dont skip a line on stdout

		


	"""
	This method is used to show the test cases used in a Proteum test session.
	"""
	def tcase_show(self, testcase_list):
		
		"""
		Args:
			testcase_list = a list witch contains the number of the test cases want to visualize
				if testcase_list is a empty list, them will apply the effect for all test_cases
		"""

		test_cases = mutant_util.list_string(testcase_list) #Convert testcase_list in a suitable string to use in Proteum

		if not testcase_list:
			statment = 'tcase -l ' + self.session
		else:
			statment = 'tcase -x %s ' % (test_cases) + self.session 

		if verbose: print '\nProteum: ' + statment
		if verbose: print "Proteum: Listing the test case for the program under test.. \n"
		os.system(statment)



	"""
	This method is used to ENABLE test cases in a test set in a Proteum session.
	"""
	def tcase_enable(self,testcase_list):
		
		"""
		Args:
			testcase_list = a list witch contains the number of the test cases want to remove
				if testcase_list is a empty list, them will apply the effect for all test_cases
		"""

		test_cases = mutant_util.list_string(testcase_list) #Convert testcase_list in a suitable string to use in Proteum

		if not testcase_list:
			statment = 'tcase -e ' + self.session
		else:
			statment = 'tcase -e -x  %s ' % (test_cases) + self.session 

		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: The set of test case for the program was changed! List of test cases enabled: %s \n' % (testcase_list)
		os.system(statment)



	"""
	This method is used to DISABLE test cases in the test set in a Proteum test session.
	"""
	def tcase_disable(self,testcase_list):
		
		"""
		Args:
			testcase_list = a list witch contains the number of the test cases want add
				if testcase_list is a empty list, them will apply the effect for all test_cases
		"""

		test_cases = mutant_util.list_string(testcase_list) #Convert testcase_list in a suitable string to use in Proteum

		if not testcase_list:
			statment = 'tcase -i ' + self.session
		else:
			statment = 'tcase -i -x %s ' % (test_cases) + self.session 

		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: The set of test case for the program was changed! List of test cases disabled: %s \n' % (testcase_list)
		os.system(statment)



	"""
	This method is used to REMOVE test cases of a test set in a Proteum test session.
	"""
	def tcase_remove(self,testcase_list):
		
		"""
		Args:
			testcase_list = a list witch contains the number of the test cases want to remove
				if testcase_list is a empty list, them will apply the effect for all test_cases
		"""

		test_cases = mutant_util.list_string(testcase_list) #Convert testcase_list in a suitable string to use in Proteum

		if not testcase_list:
			statment = 'tcase -d ' + self.session
		else:
			statment = 'tcase -d -x  %s ' % (test_cases) + self.session 

		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: The set of test case for the program was changed! List of test cases removed: %s \n' % (testcase_list)
		os.system(statment)
		


	"""
	This method is used to generate the mutants. It will modifie the mutants descriptor file by adding nem mutants.
	IMPORTANT: If a mutant has already been created it is not modified or erased "You can just change the status of that mutant"
	"""
	def muta_gen(self,operators, functions = None):
		
		"""
		Args:
			operators = a dictionary contaning the mutation operators for the mutants who want to create and a flot number who indicates the sample rate of that operator[] 
			For instance: {-u-SSDL: 1.0}  -> Will generate 100 percent of mutants for the SSDL operator.   
			functions = a list with the name of the functions that will be muted. If this parameter is not provited so muta-gen
						will mutate all the functions present in the program (include the main function) 
		"""

		statment = ''

		#If the user pass the list with the functions name, will create a string to concatenate with statment. Else unit will be just a empty string  
		#Example: list = ["func1", "func2", "func3"]  unit -> "-unit func1 -unit func2  -unit func3"
		#This will allow muta-gen creat mutants just for the specified functions  
		if functions:
			unit = ' -unit '
			unit = unit.join(functions)
			unit = ' -unit ' + unit
		else:
			unit = ''

		if  len(operators) == 0:
			statment = 'muta-gen %s -u- 1.0 0 ' % (unit) + self.program
		else:
			operators_string = list_string2(sorted([" %s %s 0" % (operator,percent) for operator,percent in operators.iteritems()])) #this converts a dict in a list then in a suitable string format to use in Proteum
			statment = 'muta-gen %s %s ' % (unit,operators_string) + self.program 
			#Sample: Dict -> {'-u-SSDL': '1.0', '-u-CCDL': '1.0', '-u-OODL': '1.0'} ; Converted in a list: ['-u-CCDL  1.0 0', '-u-OODL  1.0 0', '-u-SSDL  1.0 0'] -> The number 0 after the Key and Value pf the dict is the sample rate of mutation for each operator

		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: Generating the mutants for the program... \n'
		os.system(statment)
		


	"""
	This method is used to execute the mutants. It will modifie the mutants status to reflect its condition of live or dead.
	"""
	def exemuta_exec(self, dual= False):

		if dual:
			statment = 'exemuta -exec -dual ' + self.session  #Info about DUAL -> DELAMARO, Márcio Eduardo . Dual Mutation: The 'Save the Mutants'  Approach. In: III Brazilian Symposium on Software Quality, Brasília, 2004. p. 301-312.
		else:
			statment = 'exemuta -exec -v . ' + self.session
			#statment = 'exemuta -exec -v -trace . ' + self.session

		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: Executing mutants against the testset... \n'		
		os.system(statment)
		print '\n' #put a \n because at the end of execution proteum dont skip a line on stdout




	"""
	This method is used to execute the mutants. It will modifie the mutants status to reflect its condition of live or dead.
	"""
	def exemuta_one_exec(self,mutant):

		statment = 'exemuta -exec -v . -f %s -t %s  ' % (mutant, mutant) + self.session
		
		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: Executing mutants against the testset \n'		
		os.system(statment)
		print '\n' #put a \n because at the end of execution proteum dont skip a line on stdout




	"""
	This method is used to select a subset of mutants. Using this option of exemut is possible to select a subset of mutants.
	"""
	def exemuta_select(self,operators):
		
		"""
		Args:
			operators = It can be a DICTIONARY wich contains the mutation operators for the mutants who want to select and a flot number who indicates the sample rate for that operator
				For instance: {u-SSDL: 1.0, u-VVDL: 0.5}  -> Will select 100 percent of mutants for the SSDL operator and 50 percent of the mutants for VVDL operator.
				Or it can be a LIST wich contains the mutants who wants to select.  
		"""
		
		if not operators:
			statment = 'exemuta -select -all 1.0  ' + self.session 
		else:
			if type(operators) is types.DictType: 
				operators_string = mutant_util.list_string2(sorted([" -%s %s " % (operator,percent) for operator,percent in operators.iteritems()])) #this converts a dict in a list then in a suitable string format to use in Proteum
				statment = 'exemuta -select  %s ' % (operators_string) + self.session 
				#Sample: Dict -> {'-u-SSDL': '1.0', '-u-CCDL': '1.0', '-u-OODL': '1.0'} ; Converted in a list: ['-u-CCDL  1.0 0', '-u-OODL  1.0 0', '-u-SSDL  1.0 0'] -> The number 0 after the Key and Value pf the dict is the sample rate of mutation for each operator
			
			elif type(operators) is types.ListType:
				mutants = mutant_util.list_string(operators)
				#Convert operators in a suitable string to use in Proteum
				statment = 'exemuta -select -x %s ' % (mutants) + self.session 
			else:
				if verbose: print 'The operators source don\'t have a expected value. Operators: %s \n' % (operators)
				raise ValueError
		
		os.system(statment)
		if verbose: print '\nProteum: ' + statment	
		if verbose: print 'Proteum: The state of the mutants  was modified! Number of active mutants: %d \n' % (len(operators))		
		



	"""
	Determines that the states of all mutants will be togled. The ones that are inactive  become active and vice-versa.
	"""
	def exemuta_invert(self):
		statment = 'exemuta -invert ' + self.session
		
		os.system(statment)
		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: The mutants state was togled. Inactive mutants are active now and vice-versa. \n'
				



	"""
	This function lists all mutants generated in the console. Returns a string that contains the output 
	"""
	def muta_list(self,mutants):

		output = None
		statment = ''
		
		if not isinstance(mutants,list):
			mutants =[]
		else:
			if len(mutants) == 0:
				statment = 'muta -l ' + self.session
			else:
				mutants  = mutant_util.list_string(mutants)
				statment = 'muta -l -x %s ' % (mutants) + self.session 

		output = str(subprocess.check_output(statment, shell=True))
		return output




	#It's incomplet. Need to find a way to define where put the genereted mutant. In this stage, all file are created in the root of the program 
	"""
	This function generate the mutants specified in the list. Creates a folder with the mutants. 
	"""
	def build_mutants(self,mutants):

		statment = ''

		if not isinstance(mutants,list):
			logging.warn("W: Invalid parameter")
			mutants = []

		if not os.path.exists('Mutants'):
			os.mkdir('Mutants')

		#create all mutants
		for m in mutants:
			statment = 'exemuta -build-one -x \"%s\" ' % str(m) + self.session 
			os.system(statment)

		#Must move the generated files to the directory Mutants




	"""
	This function set the equivalent mutants.  
	"""
	def muta_equiv(self,equivalents):
		
		"""
			If equivalents is a empty list, will set all live mutants as equivalents
		"""
		statment = ''
		
		if not isinstance(equivalents,list):
			equivalents =[]
		else:
			if len(equivalents) == 0:
				statment = 'muta -equiv ' + self.session
			else:
				equivalents = mutant_util.list_string(equivalents)
				statment    = 'muta -equiv -x %s ' % (equivalents) + self.session

		statment2 = 'exemuta -exec -v . ' + self.session 

		os.system(statment)
		if verbose: print '\nProteum: ' + statment 
		if verbose: print 'Proteum: --> Some mutants were define as equivalents \n'




	"""
	This function set mutants was active.  
	"""
	def muta_active(self,mutant_list):

		"""
			If mutant_list is a empty list, will set all mutants as active
		"""
		statment = ''
		
		if not isinstance(mutant_list,list):
			mutant_list =[]
		else:
			if len(mutant_list) == 0:
				statment = 'muta -active ' + self.session
			else:
				mutant_list = mutant_util.list_string(mutant_list)
				statment = 'muta -active -x %s ' % (mutant_list) + self.session 
		
		statment2 = 'exemuta -exec -v . ' + self.session
		
		os.system(statment)
		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: --> The mutants inside mutant_list were define as active! \n'




	"""
	This function set mutants was inactive.  
	"""
	def muta_nactive(self,mutant_list):

		"""
			If mutant_list is a empty list, will set all mutants as inactive
		"""
		statment = ''
		
		if not isinstance(mutant_list,list):
			mutant_list =[]
		else:
			if len(mutant_list) == 0:
				statment = 'muta -nactive ' + self.session
			else:
				mutant_list = mutant_util.list_string(mutant_list)
				statment = 'muta -nactive -x %s ' % (mutant_list) + self.session 
		
		statment2 = 'exemuta -exec -v . ' + self.session
		
		os.system(statment)
		if verbose: print '\nProteum: ' + statment
		if verbose: print 'Proteum: The mutants inside mutant_list were define as inactive \n'


	def mutation_score(self):

		statment = 'muta -ms %s' % (self.session)

		score = str(subprocess.check_output(statment, shell=True))

		if verbose: print 'Proteum: Mutation Score: %s' % (score)