#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import time

import cProfile
import pstats

from itertools import chain

from Nodes import Server
from Proteum import Proteum

from Proteum.Util import programs
from Proteum.Util import constants
from Proteum.Util import files_util
from Proteum.Util import mutant_util


verbose = True

#@profile
def main(program, testset,compile_file, functions, equivalents, session, scheduler_adress, finish):

	if verbose: print ("I: ------------------------ Starting a new session ------------------------\n")

	#A instance of Server class. What contains the methods used to communicate with other machines
	server = None
	server = Server(scheduler_adress, program)

	#Base case. This case is True just at the end of the execution
	if finish:

			if verbose: print "I: Finishing the processer. Sendding a DISCONECT signal to Scheduler"

			#Wait two seconds
			time.sleep(2)

			#A instance of Server class sends the disconnect signal
			server.send_to_scheduler(constants.DISCONNECT, constants.SERIALIZE, [])
			
			#Closing the socket and the ZMQ context
			server.destroy()

			return 0 #exiting


	#Get the compile command used to compile the program
	compile_command = files_util.get_compile_command(compile_file)

	#A instance of Proteum class what contains the most used proteum modules
	proteum = Proteum(program,session)

	#Creates a new test session
	proteum.test_new(compile_command)

	#Get all fuctions described in the file functions.txt
	functions_list = []
	function_list = files_util.get_all_functions(functions)

	#Creates the set of mutants. The empty list indicates that will be generate mutants using all operators.
	proteum.muta_gen([],function_list)


	if verbose: print "I: Starting a new Proteum test session"
	if verbose: print "I: Creats a new test session"
	if verbose: print "I: Generate all mutants"

	mutant_dic    = {} #The Key is the Operator and the value is a List with the number of each mutant
	mutant_status = {} #The key is the mutant index and the value is a set with (Status,Causa Mortis,Operator)
	test_set_dic  = {} #The key is a index and the value is a list with the inputs


	#Populate the dictionarys with all created mutants. 
	mutant_dic,mutants_status = mutant_util.get_all_mutants(proteum.muta_list([]))

	if verbose: print "I: Compile every mutant in a dictionary"

	#Populate the dictionary with all test cases descrited in testset file.
	#The Key is the number of the testcase and the value is a List with the inputs
	test_set_dic = files_util.get_all_test_cases(testset)

	if verbose: print "I: Compile all testset in other dictionary"

	if verbose: print "I: The test session os ready to start"

	#At this point the mutantion process is ready to start
	
	request = None
	program_name = program +'.zip'
	program_file = open(program_name, 'rb')
	
	#Read the zip file as a string of bytes	
	request = program_file.read()

	#Request contains just the zip file off the program under testing with all archives inside 

	"""	The structure of the message is:
			msg[0] = The zip file of the program with all that content "Ex: cal.zip"
	""" 
	
	#At creates a Server instance, sends a READY request to the Scheduler. Will send the msg to scheduler.
	server.send_to_scheduler(constants.READY, constants.NSERIALIZE, request)
	
	if verbose: print "I: Waitting for the WORKERS connection..."

	#Should recive a confirmation response
	response = server.recive_response()

	if verbose: print response.pop(0)

	#After recive the response, just close the file. Will note be userfull anymore
	program_file.close()

	#At this point the server and workers are already connected at the scheduler and will send some REAL data

	#Information that will be sent. Contains a dictionary that describes all the mutants and another dictionary with the test cases
	request = [mutant_dic,test_set_dic]

	if verbose: print "I: Sendding a request to SCHEDULER with mutants and testset. Will wait for a response"

	#The information is ready to send for the scheduler. After send will wait for a response. Will block and wait for this response.
	server.send_to_scheduler(constants.REQUEST, constants.SERIALIZE, request)

	#At this point the server will wait until the end of the process to summarize the results contained in 'response'

	#After send a request will wait for a response..
	response = server.recive_response() #Response contains a list with all dead mutants


	if verbose: print "I: End of the process. Calculating the Mutation Score.."

	#Getting the list of equivalent mutants
	equivalents_list = files_util.get_equivalent_mutants(equivalents)

	mutants_list  = list(chain(*mutant_dic.values()))
	dead_mutants  = [str(item) for item in response]
	dead_mutants  = list(set(dead_mutants))  #Remove duplicates

	#Calculing the list of alive mutants
	not_alive_mutants = equivalents_list + dead_mutants  #list with mutants that are not alive
	alive_mutants     = [m for m in mutants_list if m not in not_alive_mutants]
	mutation_score    = mutant_util.mutation_score(mutants_list, equivalents_list,dead_mutants)


	if verbose: print '\n======================== Summary for %s =======================' % (program_name[:-4].upper())
	
	if verbose: print 'I: Live Mutants: %d  '      % (len(alive_mutants))
	if verbose: print 'I: Killed Mutants: %d'      % (len(dead_mutants))
	if verbose: print 'I: Equivalents Mutants: %d' % (len(equivalents_list))
	if verbose: print 'I: Total Mutants: %d '      % (len(mutants_list))
	if verbose: print "I: Mutantion Score: %s "    % mutation_score
	
	if verbose: print '================================================================= \n' 



if __name__ == '__main__':

	#Clear the screen
	os.system("clear");
	
	#Verify the execution
	if len(sys.argv) < 2:
		print 'Usage: python server.py scheduler_ip'
		sys.exit(0)

	#Enter in the folder 
	r = os.chdir('Experiments')
	r = os.chdir('Programs')

	#Get the IP adress from argv
	ip = str(sys.argv[1])

	#Define the address of scheduler
	scheduler_adress = "tcp://%s:5555" % (ip)

	programs_list = programs.list_programs()

	#After the last iteration off the for Loop change the value of ends to True to finish the execution of the scheduler
	finish = False

	num_tests = len(programs_list)

	for program in programs_list:

		#Creates a zip file of the program under testting
		shutil.make_archive(program, "zip", program)

		#Name of the zip
		zipname = program + '.zip'
		workdir = os.getcwd()
		
		#Define file dir and the destination dir to move the file
		filedir = str(workdir +'/'+ zipname)  #Cast to STR to avoid the issue "http://bugs.python.org/issue17153"
		end_dir = str(workdir +'/'+ program +'/' + zipname) #Cast to STR to avoid the issue "http://bugs.python.org/issue17153"
	
		#Move the zip file to the directory of the program
		shutil.move(filedir,end_dir)

		r = os.chdir(program)

		#Name of the session
		session = program

		#file what contains the testset
		testset = open('testset.txt','r')

		#file that contains the functions of the program. Will be used in mutation process
		functions = open('functions.txt','r')

		#file that contains the functions of the program. Will be used in mutation process
		equivalents = open('equivalents.txt','r')

		#file that contains the compile command for the program
		compile_file = open('compile.txt','r')
		
		#Creates a profile instance 			  						 ############################
		prof = cProfile.Profile()                 						 ############################
		
		prof.enable() #Start the profile          						 ############################

		#start the execution
		main(program, testset, compile_file, functions, equivalents, session, scheduler_adress, finish)		
		
		prof.disable() #End the profile            						 ############################
		
		#define the name of the file with the data 						 ############################
		file_name = program+'_results'             						 ############################
		file_name_raw = file_name + '_raw'         						 ############################
		prof.dump_stats(file_name_raw) #Dumps the result into a file 	 ############################

		#Save the Profile results into a human redable format 			 ############################
		arq = open(file_name,'wb')                            			 ############################
		ps = pstats.Stats(prof, stream= arq)                  			 ############################
		arq.write(str(ps.strip_dirs().sort_stats("time").print_stats())) ############################
		arq.close() #close the file 									 ############################

		#at the end of the execution close the files
		testset.close()
		functions.close()
		equivalents.close()
		compile_file.close()

		#Return to the root of the programs to open the next one.
		r = os.chdir("..")

	#After process all programs, finish becames True and execute one more time the main() to finish the scheduler execution
	else:
		#Will end the scheduler execution
		finish = True

		#Every parameter is blank because the execution will stop in the first statement of the main
		main('', '', '', '', '', '', scheduler_adress, finish)
	




