#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import zipfile

import pstats
import cProfile

from Nodes import Worker
from Proteum import Proteum

from Proteum.Util import constants
from Proteum.Util import files_util
from Proteum.Util import serialize_util
from Proteum.Util import times_util
from Proteum.Util import mutant_util


verbose = True

def main(scheduler_adress):

	if verbose: print ("\nI: ------------------------ Starting a new process ------------------------- ")

	#A instance of Server class. What contains the methods used to communicate with other machines
	worker = None
	worker = Worker(scheduler_adress)

	data = None       #The data
	strategy = ''     #Strategy used for data execution
	information  = [] #List with information of the program under testing
	program_name = '' #Name of the program under testing

	#Sends a READY request to the Scheduler, should recive a confirmation response after recordding the worker
	worker.send_to_scheduler(constants.READY, constants.SERIALIZE,['Starting'])

	#This response should be a archive with the data and strategy of the program under test
	information, data = worker.recive_data()


	information = serialize_util.decompress(information)

	#If information is empty...
	if(information[0] == ''):

		#the server still not connected
		if verbose: print data.pop()
		time.sleep(3) #wait 3 seconds before try again
		return '', '', True

	#Information is a list, the server is already connected to the scheduler and Worker should process the response
	else:

		#The information cames in utf-8 so, first of all decode it
		program_name = information.pop(0).decode('utf-8')
		strategy = information.pop(0).decode('utf-8')


	if verbose: print "I: Will recive data from Scheduler when all workers connect."

	#Get the zip file with all data to process
	program_zip = data.pop()

	#Create the file obj
	program_file = open(program_name+'.zip','w')

	#Write the content recived in that file
	program_file.write(program_zip)

	#close the program_file
	program_file.close()

	#Get the directory
	cdir = os.getcwd()
	program_location = str(cdir + '/' + program_name) #Cast to STR to avoid the issue "http://bugs.python.org/issue17153"

	#Get the zip file the extract it. Will create a new directory
	zipf = zipfile.ZipFile(program_name+'.zip')
	zipf.extractall(program_location)

	#Get inside the new directory created
	r = os.chdir(program_name)

	if verbose: print "I: Starting the mutation test."

	#Open the functions file
	functions_file = open('functions.txt','r')

	#file that contains the compile command for the program
	compile_file = open('compile.txt','r')
	compile_command = files_util.get_compile_command(compile_file)

	#Get all fuctions described in the file functions.txt
	functions_list = []
	function_list = files_util.get_all_functions(functions_file)

	#Define the name of the session
	session = program_name

	#A instance of Proteum tool this class contains the most used proteum modules features
	proteum = Proteum(program_name, session)

	#Creates a new test session
	proteum.test_new(compile_command)

	#Creates the set of mutants. The empty list indicates that will be generate mutants using all operators, the function list indicates the functions that will be mutated
	proteum.muta_gen([], function_list)

	#Close the functions file
	functions_file.close()

	#Close the compile file
	compile_file.close()

	#At this point every worker have the program. Now the worker need recive the data to process it..

	#The execution will occur according to the approach used. It can  be static, dynamic or use both.

	test_set = [] #The dictonary is almost every time converted into a list
	mutants_list = [] #List used to store the mutants recived from scheduler
	mutants_executed = [] #Will save all mutants executed for this worker

	print "\nI: Ready to START. Sendding syncronization signal to SCHEDULER..."

	#Send trash just to notify the scheduler before start..
	worker.send_to_scheduler(constants.SYNCHRONIZE, constants.SERIALIZE,['SYNCHRONIZE'])

	#static
	if(strategy == constants.DMBO or strategy == constants.DTC):

		#If the strategy is dmbo
		if (strategy == constants.DMBO):


			#Process the request appropriately appropriately
			mutants_list,test_set = worker.process_dmbo()

			if verbose: print "I: Number of mutants: ", len(mutants_list)
			if verbose: print "I: Number of test cases: ", len(test_set)

			#add the testcases in proteum test set
			for tc in test_set:
				proteum.tcase_add(tc)

			#If the list of mutants is bigger than 1000, split into minor lists to avoid the problem of the character limite in command line terminal
			if (len(mutants_list) > 1000):

				#Get the div and the mod
				n,r = divmod(len(mutants_list),1000) 

				#If the mod is != of 0 increase the value of 'n' in 1
				if (r > 0):
					n = n+1

				#Will break the mutants_list into 'n' pieces
				mutants_list = mutant_util.chunk_list(mutants_list,n)

				print 'Number of lists created: ', n
			
			else:

				#Just envelop the list inside other list
				mutants_list = [mutants_list]

			#run over each list and execute it
			for lista in mutants_list:
				
				#Select the mutants that wants to execute. All the others are considered inactives
				proteum.exemuta_select(lista)

				#Then, finally execute the testcases
				proteum.exemuta_exec()

				#Number of mutants executed
				mutants_executed = mutants_executed + lista


		#DTC
		else:  #The strategy will change de order of the data

			#Process the request appropriately appropriately
			mutants_list,test_set = worker.process_dtc()

			if verbose: print "I: Number of mutants: ", len(mutants_list)
			if verbose: print "I: Number of test cases: ", len(test_set)

			#add the testcases in proteum test set
			for tc in test_set:
				proteum.tcase_add(tc)

			#Then, finally execute the testcases
			proteum.exemuta_exec()

			#Number of mutants executed is always the number of mutants in DTC
			mutants_executed = mutants_list


		if verbose: print 'I: Number of mutants executed:', len(mutants_executed)

	#Dynamic
	elif(strategy == constants.GMOD or strategy == constants.GTCOD):

		time.sleep(2) #This sleep will avoid starvation

		#If it's dynamic
		if(strategy == constants.GMOD):

			#Will execut the data on demand. At the end return a list with the mutants processeds
			test_set,mutants_executed = worker.process_gmod(proteum)

		#It's also dynamic but will change the order of the data
		elif(constants.GTCOD):

			#Will process the data receiving testcases dynamically.
			test_set,mutants_executed = worker.process_gtcod(proteum)


		#At the end of the dynamic execution if verbose: print the number of mutants executed
		if verbose: print 'I: Number of mutants executed:', len(mutants_executed)

	#If it uses both (PEDRO)
	elif (strategy == constants.PEDRO):

		#At the end of the execution return the list of executed mutants
		test_set, mutants_executed = worker.process_pedro(proteum)

	#Neither
	else:
		if verbose: print 'E: Invalid strategy of data distribuition. Check the parameters of the Scheduler!'
		sys.exit(0)


	#Now should calculate the Mutation Score and send back to the scheduler and finish the execution

	if verbose: print "I: Finish the processing. Will process the data and send the result to scheduler"

	#Populate the dictionarys with all created mutants
	mutant_dic,mutants_status = mutant_util.get_all_mutants(proteum.muta_list([]))

	#For every mutant executed, will check it status. If it's dead then add to the list of dead mutants. #Every mutant have this patnner of information (Status, Causa Mortis, Operator). So to know if it's dead, just check if the status is equals to Dead
	dead_mutants  = [m for m in mutants_executed if constants.DEAD in mutants_status[m][0]]

	#Mutants processeds that arent in dead_mutants
	alive_mutants = [m for m in mutants_executed if m not in dead_mutants]

	if verbose: print '\n======================== Summary ================================'
	if verbose: print "I: Number of mutants processed: %d " % (len(mutants_executed))
	if verbose: print "I: Number of test cases used: %d " %  (len(test_set))
	if verbose: print "I: Number of dead mutants: %d " %  (len(dead_mutants))
	if verbose: print "I: Number of alive mutants: %d " %  (len(alive_mutants))
	if verbose: print '=================================================================\n'

	#Now send the list of dead mutants to scheduler and finish the execution
	worker.send_to_scheduler(constants.REPLY, constants.SERIALIZE, dead_mutants)

	if verbose: print 'I: Endding the process..'

	#At the end come back to the directory of origin
	r = os.chdir('..')

	return program_name, strategy, True



if __name__ == '__main__':

	os.system("clear")

	#Verify the execution
	if len(sys.argv) < 2:
		print 'Usage: python worker.py scheduler_ip'
		sys.exit(0)

	d = "Worker"

	#Verifys if the directory exists and create it.
	if not os.path.exists(d):
		os.makedirs(d)

	#Creates a directory named "Worker". Will made the mutation process inside this directory
	r = os.chdir(d)

	#Create a random Worker directory to save the files related to that execution
	#t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	t = random.randrange(1,10000+1)

	#The name of the folder will be Worker+datatime
	d = "Worker" + str(t)

	#Creates the directory
	if not os.path.exists(d):
		os.makedirs(d)

	#Get inside
	r = os.chdir(d)

	#Get the ip adress from argv
	ip = str(sys.argv[1])

	#Adress of the scheduler
	scheduler_adress = "tcp://%s:5555" % (ip)


	#Controls the execution
	execute = True

	#While have programs to execute..
	while execute:

		#Creates a profile instance											############################
		prof = cProfile.Profile()											############################

		prof.enable() #Start the profile 									############################

		#Start the main execution
		program_name, strategy, execute = main(scheduler_adress)

		prof.disable() #End the profile 									############################

		#define the name of the file with the data 							############################
		file_name = program_name + '_' + strategy 							############################
		file_name_raw = file_name + '_raw'									############################
		prof.dump_stats(file_name_raw) #Dumps the result into a file 		############################

		#Save the Profile results into a human redable format				############################
		arq = open(file_name,'wb')											############################
		ps = pstats.Stats(prof, stream= arq)								############################
		arq.write(str(ps.strip_dirs().sort_stats("time").print_stats()))    ############################
		arq.close() #close the file                                         ############################

	#Return to the root of the programs to open the next one.
	r = os.chdir("..")
