#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import sys
import zmq

from Proteum.Util import mutant_util
from Proteum.Util import constants
from Proteum.Util import serialize_util
from Proteum.Util import times_util

verbose = True

class Worker():

	"""
		Args:
			context     = ZQM context
			scheduler   = The address string of the scheduler. This has the form ‘protocol://interface:port’, for example ‘tcp://127.0.0.1:5555’ 
			worker_sock = socket to connect to scheduler
			timeout     = pooler timeout
			verbose     = logging register
			reply_to    = adress to reply
	"""

	scheduler   = None
	context     = None
	worker_sock = None 
	timeout     = 2500



	"""
		Constructor: Inicialize worker state
	"""
	def __init__(self, scheduler):

		self.scheduler = scheduler
		self.context = zmq.Context()
		self.poller = zmq.Poller()

		self.connect_to_scheduler()


	"""
		Connect to scheduler
	"""
	def connect_to_scheduler(self):


		#Creats a ZQM worker socket (Dealer type) and connect it to scheduler
		self.worker_sock = self.context.socket(zmq.DEALER)
		self.worker_sock.linger = 0
		self.worker_sock.connect(self.scheduler)

		#Register the worker_sock for I/O monitoring.
		self.poller.register(self.worker_sock, zmq.POLLIN)

		if verbose: print "I: Connecting to scheduler at %s..." % self.scheduler


	"""
		This method waits for a connection. When recive it, just return the adress
	"""
	def recive_data(self, timeout = None):
		
		data = None
		information = None

		print "I: Waitting for information from SCHEDULER.."

		try: #Waits for connection

			items = self.poller.poll(timeout)

			#If recive something
			if items:
				data = self.worker_sock.recv_multipart()

				"""	Structure of the message recived is: [serialize?, information, data]
					serialize   = Specifies if need decompress or not the data
					information = Its a list that indicate the name of the program and the approach used to process the data
					data        = The data  
				"""

				serialize = data.pop(0) #Need deserialize?
				information  = data.pop(0) #Alway inform the strategy

				if(serialize == constants.SERIALIZE):

					#remove the data from the list to decompress it 
					data = data.pop(0) #before: [data] after: data

					#Revice a message as a list of frame objects. Decompress it.
					data = serialize_util.decompress(data)
								
		except KeyboardInterrupt:
			if verbose: print "I: The execution was interrupted by keyboard! Restart the process.."
			sys.exit(1)

		return information,data


	"""
		Send message to scheduler 
	"""
	def send_to_scheduler(self, command, serialized, msg=None):

		"""
		Args:
			command   = Kind of information sended (ready, request, reply, disconnect "see commands.py")
			serialize = specifies if the data need to be serialized
			msg       = the data 
		"""
		
		if msg is None:
			msg = []

		if (serialized == constants.SERIALIZE):
	
			#If request is not a list creat a list if the content of request
			if not isinstance(msg,list):
				msg = [msg]

			#At this point msg already have the content 

			"""	The structure of the message is:
					msg[0] = Empty frame to emulate the "Request Socket" 
					msg[1] = Identifys who is sending the message
					msg[2] = The kind of command
					msg[3] = empty delimiter -> This cover the program_name in server
					msg[4] = The data 
			"""

			#Before send the message need to serialize it
			msg = serialize_util.compress(msg)

		msg = ['',constants.WORKER, command, serialized, '', msg]

		if verbose: print "I: Talking with scheduler at: %s. Type of command: %s " % (self.scheduler, command.upper())
		
		#Send request to the scheduler. Already knows where to send the message because of the line 54.		
		self.worker_sock.send_multipart(msg)


	"""
		ZQM context destroy
	"""
	def destroy(self):

		if verbose: "I: Closing the connections and shutting down the WORKER.." 
		self.context.destroy(0)



	"""
		This method is used to process dmbo approach
	"""
	def process_dmbo(self):

		if verbose: print "I: Reciving data from Scheduler..." 
		if verbose: print "I: Using: Distribute Mutants Between Operators Algorithm \n"

		information,data = self.recive_data()
		
		#data is something like [{tcaseID: [inputs]}, mutantID, mutantID, .. ], getting just the dict in tcase because it's always the same
		testdict = data.pop(0)
		mutants_list = data  #After remove the testset, data have only the mutants ID
		test_set = []

		#remove de u' from the unicode format
		mutants_list = [str(item) for item in mutants_list]

		for tc in testdict.values():
			tc = [str(item) for item in tc]
			test_set.append(tc)

		return mutants_list, test_set



	"""
		This method is used to process dtc approach
	"""
	def process_dtc(self):

		if verbose: print "I: Reciving data from Scheduler..." 
		if verbose: print "I: Using: Distribute Test Cases Algorithm \n"

		information,data = self.recive_data()
		mutants_list = data.pop(0) #First element is a list with all mutants
		testset_list = data #After remove the list of mutants there's only the test cases for that chunk
		test_set     = []

		#remove de u' from the unicode format
		mutants_list = [str(item) for item in mutants_list]
		
		#remove de u' from the unicode format
		for tc in testset_list:
			tc = [str(item) for item in tc]
			test_set.append(tc)

		return mutants_list, test_set	




	"""
		This method is used to process gmod approach
	"""
	def process_gmod(self, proteum):

		"""
			Args:
				proteum = A instance of the proteum class used as interface to make the calls of the proteum modules
		"""

		if verbose: print "I: Reciving data from Scheduler..."
		if verbose: print "I: Using: Given Mutants On Demand Algorithm \n"
		
		test_set = []
		mutant   = None
		mutants_list = []
		compute = True #This variable is used to avoid unnecessary computing

		#Loop for revice data
		while (True):
			
			#Try send a request, if the scheduler don't want more requests, will stop because of the timeout
			self.send_to_scheduler(constants.REQUEST, constants.SERIALIZE, [])
			
			#Response
			information,data = self.recive_data()
			
			#The last iteration data will be None
			if data:
				mutant = str(data.pop(0)) #convert to string to remove the 'u' from unicode format
				mutants_list.append(mutant) #At the end will have a list with the mutants executed
				
				#The test set is always the same, so execute this operation just one time						
				if compute:

					compute = False #in next iteration will avoid this block

					testdict = data.pop() #recive the inputs in a dict

					#Removing the 'u' from unicode format and add to proteum session test
					for tc in testdict.values():
						tc = [str(item) for item in tc]
						proteum.tcase_add(tc)
						test_set.append(tc)

				if verbose: print "I: Mutant: ", mutant
				if verbose: print "I: Test cases: ", test_set
				
				#Leave all mutants selected and execute just one
				proteum.exemuta_one_exec(mutant)


			#When data be None will break the loop
			else:

				#Mutants executed
				mutants_executed = mutants_list
				return test_set, mutants_executed



	"""
		This method is used to process gtcod approach
	"""
	def process_gtcod(self,proteum):

		"""
			Args:
				proteum = A instance of the proteum class used as interface to make the calls of the proteum modules
		"""

		if verbose: print "I: Reciving data from Scheduler..."
		if verbose: print "I: Using: Given Test Case On Demand Algorithm \n"
		
		tcase = None
		test_set = []
		mutants_list = []
		
		compute = True #This variable is used to avoid unnecessary computing
		
		#Loop for revice data
		while (True):

			#Try send a request, if the scheduler don't want more requests, will stop because of the timeout
			self.send_to_scheduler(constants.REQUEST, constants.SERIALIZE,[])

			#Response
			information,data = self.recive_data()
			
			#Recive something
			if data:

				mutants_list = data.pop(0)
				tcase = data.pop(0)

				#This block is need to execute just one time, compute avoid unnecessary computing 
				if compute:
					compute = False	#Compute is false, so next iteration will jump this block					
					
					#remove de u' from the unicode format
					mutants_list = [str(item) for item in mutants_list]

				#remove the 'u' from the input
				tcase = [str(item) for item in tcase]

				if verbose: print "Number of mutants: ", len(mutants_list)
				if verbose: print "Test case: ", tcase

				#Add the testcase to the session test
				proteum.tcase_add(tcase)
				test_set.append(tcase)

				#At the end execute the test case agains the mutants
				proteum.exemuta_exec()
			
			#When data is None get out the while
			else:

				#Mutants executed
				mutants_executed = mutants_list
				return test_set, mutants_executed  #get out off the while



	"""
		This method is used to process pedro approach
	"""
	def process_pedro(self,proteum):

		"""
			Args:
				proteum = A instance of the proteum class used as interface to make the calls of the proteum modules
		"""

		if verbose: print "I: Reciving data from Scheduler... "
		if verbose: print "I: Using: Parallel Execution Withe Dynamic Ranking and Ordering Algorithm"
		
		if verbose: print "I: Starting Phase One..."

		compute = True #This variable is used to avoid unnecessary computing
		
		#First it's executes statically 
		information,data = self.recive_data()

		testdict = data.pop(0)
		test_set = []
		mutants_list = data

		#remove de u' from the unicode format
		mutants_list = [str(item) for item in mutants_list]

		#Removing the 'u' from the inputs of the testcase
		for tc in testdict.values():
			tc = [str(item) for item in tc]
			proteum.tcase_add(tc) #add the testcases in proteum test set
			test_set.append(tc)


		print 'Number of mutants recived: ',len(mutants_list)

		#If the list of mutants is bigger than 1000, split into minor lists to avoid the problem of the character limite in command line terminal
		if (len(mutants_list) > 1000):

			#Get the div and the mod
			n,r = divmod(len(mutants_list),1000) 

			#If the mod is != of 0 increase the value of 'n' in 1
			if (r != 0):
				n = n+1

			#Will break the mutants_list into 'n' pieces
			mutants_list = mutant_util.chunk_list(mutants_list,n)

			print 'Number of lists created: ', n

		else:

			#Just envelop the list inside other list
			mutants_list = [mutants_list]

		mutants_executed = []
		
		#run over each list and execute it
		for lista in mutants_list:

			if verbose: print "I: Number of mutants: ", len(lista)
			if verbose: print "I: Number of test cases: ", len(test_set)
			
			#Select the mutants that wants to execute. All the others are considered inactives
			proteum.exemuta_select(lista)

			#Then, finally execute the testcases
			proteum.exemuta_exec()

			mutants_executed = mutants_executed + lista #will save the mutants executed in the first and second phase


		#Second phase
		if verbose: print "\nI: Starting Phase Two... "
		
		while (True):

			#Try send a request, if the scheduler don't want more requests, will stop because of the timeout
			self.send_to_scheduler(constants.REQUEST, constants.SERIALIZE, [])

			#Response
			information,data = self.recive_data()
			
			if data:

				testdict = data.pop(0) #Just remove from data. Will not use anymore
				mutants_list = data

				#remove de u' from the unicode format
				mutants_list = [str(item) for item in mutants_list]

				#Select just the mutant recived
				proteum.exemuta_select(mutants_list)

				#Execute all test cases with that mutant
				proteum.exemuta_exec()

				#Update the list of executed mutants
				mutants_executed = mutants_executed + mutants_list


			#When data is None get out the while
			else:
				if verbose: print "I: Will not ask for more data"
				if verbose: print 'I: Number of mutants executed:', len(mutants_executed)
				return test_set, mutants_executed #get out off the while