#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import cProfile
import pstats

from Nodes import Scheduler
from Proteum.Util import constants


verbose = True

def main(address,num_workers, strategy):
	
	scheduler = None
	scheduler = Scheduler(num_workers,strategy, strategy)

	#Bind the scheduler at the localhost and port 5555
	scheduler.bind(address)
	
	#Start is the main method of scheduler. It will wait for conections of the Server and Workers
	scheduler.start()



if __name__ == '__main__':

	os.system("clear");

	#Verify the execution
	if len(sys.argv) < 3:
		print 'Usage: python scheduler.py algorithm[dmbo, dtc, gmod, gtcod, pedro] num_workers'
		sys.exit(0)

	if verbose: print "(I: ------------------------ Starting a new connection ---------------------------)"

	address     = "tcp://*:5555"
	strategy    = str(sys.argv[1]) #Algorithm used
	num_workers = int(sys.argv[2]) #Number of computers that will execute the mutants


	#Creates a profile instance 			  						 ############################
	prof = cProfile.Profile()                 						 ############################
	
	prof.enable() #Start the profile          						 ############################

	#start the execution
	main(address,num_workers, strategy)
	
	prof.disable() #End the profile            						 ############################
	
	#define the name of the file with the data 						 ############################
	file_name = 'scheduler_'+strategy+'_results'					 ############################
	file_name_raw = file_name + '_raw'         						 ############################
	prof.dump_stats(file_name_raw) #Dumps the result into a file 	 ############################

	#Save the Profile results into a human redable format 			 ############################
	arq = open(file_name,'wb')                            			 ############################
	ps = pstats.Stats(prof, stream= arq)                  			 ############################
	arq.write(str(ps.strip_dirs().sort_stats("time").print_stats())) ############################
	arq.close() #close the file 									 ############################
