#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import zmq
import time

from itertools import chain
from binascii import hexlify

from Proteum import operators
from Proteum.Util import constants
from Proteum.Util import serialize_util

verbose = True

class Scheduler():

	"""
		Args:
			context      = ZQM context
			socket       = Socket for servers & workers
			poller       = ZQM Poller
			services     = known services
			waiting_list = dictionary that contains the adress of the workers and the server
			program_info = scheduler recives the name of the program, list of fuctions and a copy of the program to spread to the workers
			server        = Controls if the scheduler is connected to server
	"""

	context      = None
	socket       = None
	poller       = None
	timeout      = 2005
	waiting_list = None
	program_info = None
	num_workers  = None
	server       = False
	replys       = 0

	connections  = 1

	result       = []
	strategy     = ''
	program_name = ''
	new_connections = True
	session      = None
	


	"""
	Constructor: Inicialize the scheduler state
	"""
	def __init__(self, num_workers, strategy, server=False):

		self.context       = zmq.Context() 
		self.socket        = self.context.socket(zmq.ROUTER)
		self.socket.linger = 0
		self.poller        = zmq.Poller()
		self.poller.register(self.socket, zmq.POLLIN)

		self.timeout      = 2005
		self.waiting_list = {}
		self.program_info = None
		self.replys       = 0
		
		self.connections = 1
		
		self.num_workers  = num_workers
		self.server       = False
		self.strategy     = strategy
		self.program_name = ''
		self.result       = []
		self.new_connections = True
		self.session      = None


	"""
		Bind scheduler to endpoint, can be called multiple times.
		Use a single socket for both servers and workers.
	"""
	def bind(self, endpoint):

		"""
		Args:
			endpoint = The address string of the scheduler. This has the form ‘protocol://interface:port’, for example ‘tcp://127.0.0.1:5555’
		"""

		self.socket.bind(endpoint)

		if verbose: print "I: The SCHEDULER is actived at %s" % endpoint



	"""
		This method is used to restart the variables of the Scheduler
	"""
	def rebuild_scheduler(self):
		"""
			Args:
				Dont take any args.
		"""		
		self.timeout      = 2005
		self.program_info = None
		self.replys       = 0
		
		self.connections  = 1
		
		self.num_workers  = self.num_workers
		self.strategy     = self.strategy
		self.program_name = ''
		self.result       = []
		self.server       = False
		self.new_connections = True
		
		if verbose: print 'I: Restarting the SCHEDULER Status.. Ready to another test execution.'



	"""
		Main loop for the scheduler
	"""
	def start(self):

		while self.new_connections:

			if verbose: print 'I: Waitting for new conections..'

			adress, data = self.recive_request()
				
			"""	Structure of the DATA recived is: [sender_type, command, serialized, data ]
					sender_type = Identifys who is sending the message 'see constants.py'
					command     = The kind of command  'see constants.py'
					serialized  = need decompress it?
					data        = The data  
			"""

			#Dequeue the sender information from the msg [sender_type, command ,[msg]]
			sender_type = data.pop(0)

			#Dequeue command information
			command = data.pop(0)
			
			if verbose: print 'I: Details: Connection from %s. Type of command: %s' % (sender_type.upper(),command)
			
			#Dequeue serialized
			serialize = data.pop(0)

			#data have [info, request], get just request and let info inside data for future use.
			request = data.pop(1) #[data]

			#Decompress request
			if (serialize == constants.SERIALIZE):
				request = serialize_util.decompress(request)

			#It's a server?
			if (constants.SERVER  == sender_type):

				#Get the name of the program under testing. 
				self.program_name =data.pop(0)

				#Add server in waitting list
				self.process_server(adress, command, request)
			

			#It's a worker?
			elif (constants.WORKER == sender_type):

				#Process the worker 
				self.process_worker(adress, command, request)



	"""
		This method is used to send a broadcast msg to all workers registred in scheduler
	"""
	def broadcast_workers(self, serialize, data):

		"""
			Args:
				data       = the data to send
				serialize = especifies a constant that will serialize or not the data [constants.SERIALIZE or constants.NSERIALIZE]
		"""

		#Send the information to the workers

		#Get all workers connected
		workers_addr = self.waiting_list[constants.WORKER].values()

		#Send for each one the info to start the process
		for i in xrange(len(workers_addr)):
			worker = workers_addr[i][0]
			self.send_msg_worker(worker, serialize, data)



	"""
		This methods is used to syncronize the workers and to recive some kind of information from them
	"""
	def syncronize_workers(self):

		recived = []
		
		if verbose: print "I: Synchronizing Worker..."		
	
		while (self.connections < self.num_workers):
			
			worker,data = self.recive_request()

			#Only counts if recive a SYNCHRONIZE signal.. 
			if(constants.SYNCHRONIZE in data):
				recived.append(data)
				self.connections += 1

			if verbose: print "I: Number of Workers syncronizeds %d of %d" % (self.connections, self.num_workers)

			if(self.connections == self.num_workers):
				break

		return recived



	"""
		This method waits for a connection. When recive it, just return the adress
	"""
	def recive_request(self):

		msg     = None
		address = None
		
		try: #Waits for connection
			items = self.poller.poll()

			#If recive something
			if items:

				if verbose: print 'I: Recived a new connection!'

				msg = self.socket.recv_multipart()

				#Recive this message just to know who is avaliable

				"""	Structure of the message recived is: [sender_adr, '', machine, command, serialize, data ]
					address = Adress of the requester
					empty   = empty frame to emulate REQ socket
					machine = Identifys who is sending the message
					command = The kind of command  'see constants.py'
					serialized = need decompress it?
					data    = The data|Request  
				"""

				address  = msg.pop(0) #adress
				empty    = msg.pop(0) #Frame delimiter

			else:
				if verbose: print "E: Invalid message.. Aborting.."
				sys.exit(0)
				
		except KeyboardInterrupt:
			if verbose: print "I: The execution was interrupted by keyboard! Restart the process.."

		return address, msg



	"""
		Send a msg to worker machine. 
	"""
	def send_msg_worker(self, machine, serialize,data=None):
		
		"""
		Args:
			machine   =  Identifys the machine for send the msg (Address)  
			serialize = specifies if the data need to be serialized
			data       =  Data
		"""

		if data is None:
			data = []

		#Inform strategy and the program name when not serialize the data.
		information = serialize_util.compress([self.program_name,self.strategy])  
		
		if(serialize == constants.SERIALIZE):
			
			if not isinstance(data, list):
				data = [data]

			#Before send it using json need serialize it. 
			data = serialize_util.compress(data) 
		
		# Stack routing the envelopes to start of message
		msg = [machine, serialize, information, data] 

		if verbose: print "I: Sending data to WORKER: %s " % (hexlify(machine))

		#Sending using multipart
		self.socket.send_multipart(msg)



	"""
		Send a msg to server machine. 
	"""
	def send_msg_server(self, serialize,msg=None):
		
		"""
		Args:
			machine  =  Identifys the machine for send the msg (Address)  
			serialize = specifies if the data need to be serialized
			msg      =  Data
		"""

		if msg is None:
			msg = []

		if(serialize == constants.SERIALIZE):

			if not isinstance(msg, list):
				msg = [msg]

			#Before send it using json, first off all, nedd to serialize it. 
			msg = serialize_util.compress(msg) 
		
		#Get the server address
		server_addr = self.waiting_list[constants.SERVER].values()[0][0]

		# Stack routing the envelopes to start of message
		msg = [server_addr, serialize, msg] 

		if verbose: print "I: Sending data to SERVER: %s " % (hexlify(server_addr))

		#Sending using multipart
		self.socket.send_multipart(msg) 



	"""
		Process a request coming from a server
	"""
	def process_server(self,sender_adr,command, request):

		"""
		Args:
			sender_adr =  Adress of who is sending the message
			command    =  How process the data   
			request    =  [Data]
		"""

		if verbose: print "I: Handling the SERVER connection. Commad type: %s" % (command.upper())

		#The processes is starting.. should add the server to the list of computers and save a copy of the program
		if (command == constants.READY):

			#Add the server to the list of machines and send a OK as response.
			self.waiting_list[constants.SERVER] = {}
			self.register_computer(constants.SERVER,sender_adr)

			#request[0] = The zip file with data of the program under testing 
			self.program_info = request

			#Now can recive conections from Workers
			self.server = True

			#There is a session of test active
			self.session = True

			if verbose: print "I: SERVER connected! SCHEDULER ready to send data to WORKERS."
		
					
		elif (command == constants.REQUEST):

			#Blocking start method the receipt of new connections while process the data
			self.new_connections = False

			if verbose: print "I: Will spread the information to WORKERS.."

			#Process the data
			self.workload_distribution(request)
			
			#Ready to acept new connections 
			self.new_connections = True

			if verbose: print "I: Distribution process FINISHED. Will begun the data collection process."

			#Refresh the workers list before finish to aviod a asynchronous error in scheduler state "Correção coincidente. Inserindo um defeito para corrigir outro :D"
			self.waiting_list[constants.WORKER] = {}

			if verbose: print "I: SCHEDULER flush the list of WORKERS"


		elif(command == constants.DISCONNECT):

			#When Server ask to disconnect, then scheduler ends the process.
			if verbose: print "I: Recive a DISCONECT signal. Informing to WORKERS.."

			#Send a disconnect signal to all workers registreds 
			self.broadcast_workers(constants.NSERIALIZE, constants.DISCONNECT)
			
			time.sleep(1) #wait 1 second
			
			self.send_msg_server(constants.NSERIALIZE,'M: SCHEDULER said: WORKERS DISCONNECTED. SCHEDULER was turned off with sucess!')

			if verbose: print "I: Finishing the process and closing the SCHEDULER.."

			#Closing the sockets and ZMQ context
			self.destroy()

			self.new_connections = False
			

		else:
			if verbose: print "E: Invalid message:"



	"""
		Process message sent to scheduler by a worker
	"""
	def process_worker(self, sender_adr, command, data):

		"""
		Args:
			sender_adr =  Wserialize sending the message
			command    =  How process the data
			msg        =  [Data]
		"""

		if (constants.READY == command):

			if verbose: print "I: Handling the WORKER connection!"

			#If the server is connected..
			if(self.server):

				#Add the worker to the queue of avaliable workers waiting for some work
				self.register_computer(constants.WORKER, sender_adr)

				#Get the number of workers connected till the momment			
				len_workers = len(self.waiting_list[constants.WORKER].keys())

				print 'I: Number of WORKERS connecteds: ', len_workers

				#If the number of workers connected is equals to the number of workers expected, then release the server to continue the execution
				if(len_workers == self.num_workers):

					#Send the program under testing to all workers registred
					self.broadcast_workers(constants.NSERIALIZE,self.program_info)

					#Send the confirmation to server. Now all workers are conected!
					self.send_msg_server(constants.SERIALIZE,'M: SCHEDULER said: Recive a copy of the program with sucess!')

					if verbose: print "I: All computers registred. Ready to start the Parallel Mutation Process."


			#If the server is not connected..
			else:

				#Informe Message to Worker
				data = "M: SCHEDULER said: You Shall Not Pass!! Wait for the conection of the SERVER.."
				self.send_msg_worker(sender_adr,constants.SERIALIZE,data)

				if verbose: print "I: Connection from WORKER refused! Waitting for the SERVER..."
		

		#Scheduler is never watting this kind of command in this point. So it's ignored
		elif (constants.REQUEST == command):

			#Returns a None value to Worker
			self.send_msg_worker(sender_adr, constants.SERIALIZE, None)
			if verbose: print 'W: This REQUEST was IGNORED. Data is None'


		#Only workers can send a reply for scheduler. It1s the end of the process
		elif (constants.REPLY == command):

			if verbose: print "I: Getting all the data! Will sent the result to SERVER..."

			#At the end of the compute process the Scheduler need send this reply to Server
			self.result = self.result + data #build the result
			self.replys = self.replys + 1    #At every reply increase the variable to know if recive all the data expected

			if verbose: print "I: %d of %d results collected from Workers" % (self.replys, self.num_workers)

			#When recive everything, send it to the Server
			if(self.replys == self.num_workers):

				#if verbose: print "I: Receiving REPLY from WORKER! Summarizing the results..."
				print "I: Receiving REPLY from WORKER! Summarizing the results..."
				
				#Send the confirmation to server. Now all workers sent the result!
				self.send_msg_server(constants.SERIALIZE,self.result)

				#Restart the default values
				self.rebuild_scheduler()
		
		#When workers want start their service they syncronize first to avoid that the scheduler sends data erroneously 
		elif (constants.SYNCHRONIZE == command):
			
			if(self.server):
				self.syncronize_workers() #Just increment the syncronize counter
			else:
				if verbose: print "W: Syncronization signal ignored. Server still not connected!"

	
		else:
			if verbose: print "E: Invalid message:"



	"""
		This machine is now registed and waiting for work.
	"""
	def register_computer(self, machine_type ,machine_adr):

		"""
		Args:
			machine_type = 'server' or 'worker'
			machine_adr  = The address string of the machine. This has the form ‘protocol://interface:port’, for example ‘tcp://127.0.0.1:5555’
		"""

		#Create a identity for that machine
		identity = hexlify(machine_adr)

		#Get the dictionary with the registred server or workers
		machines_dic = {}
		machines_dic = self.waiting_list.get(machine_type)

		#See if the dictionary was already created
		if machines_dic is not None:

			#See if that machine already exists
			machine = machines_dic.get(identity)

			#If it not exist, add to the waiting list
			if (machine is None):

				#Create the machine
				machine = [machine_adr]

				#Add that machine to the dictionary of machines
				machines_dic[identity] = machine

				#update the waiting dic list
				self.waiting_list[machine_type] = machines_dic

		else: 

			#The dictionary for that type of machine don't exist. So create and add the machine to the dic.			
			machine = [machine_adr]
			machines_dic = {}
			machines_dic[identity] = machine
			self.waiting_list[machine_type] = machines_dic

		if verbose: print "I: Registering a new machine: %s" % identity



	"""
		Invoke one of the workload balance algorithms and distribute the data
	"""
	def workload_distribution(self,data):
		"""
		Args:
			data =  At this point data contains just the set of mutants and the set of test cases
		"""
		
		print "I: Syncronizing the workers.."

		self.syncronize_workers()

		if verbose: print "I: Starting the load balance process. Selected approach: %s " % (self.strategy.upper())

		mutantset = data.pop(0)  #Dict: {op:[mut_id]} -> u-ORSN: [528, 529, 530], u-OCNG: [323, 324, 325], u-OEAA: [326, 327, 328]
		testset   = data.pop(0)  #Dict: {id:[inputs]} -> 10: [7, 24, 9, 24, 1963] 
		results = None

		#Get the number of workers registred.. 
		#For that, get the length of the keys registred in the dictionary of workers
		len_workers = len(self.waiting_list[constants.WORKER].keys())

		#Choosing the approach
		if   (self.strategy == constants.DMBO):
			results = self.dmbo(mutantset, testset, len_workers) 

		elif (self.strategy == constants.DTC):
			results = self.dtc(mutantset, testset, len_workers) 

		elif (self.strategy == constants.GMOD):
			results = self.gmod(mutantset, testset)

		elif (self.strategy == constants.GTCOD):			
			results = self.gtcod(mutantset, testset)

		elif (self.strategy == constants.PEDRO):
			results = self.pedro(mutantset, testset, len_workers, len_workers) #  PEDRO algorithm needed a configuration parameter. This parameter was established as the number of remoteExecutor nodes.

		if results:
			return results



	"""
		Disconnect all workers, destroy context.
	"""
	def destroy(self):
		self.context.destroy()



	"""
		Distribute mutants between operators Algorithm 
	"""
	def dmbo(self,mutant_set,test_set,len_workers ):
		
		"""
		Args:
			mutant_set  = dictionary containing all mutants relateds to the operators -> {Operator(Key): [Mutant list](Value)}
			test_set   	= dic with all the test cases. Every testcase has a id as key -> {id:[inputs]} -> 10: [7, 24, 9, 24, 1963]
			len_workers = number of processors avaliable
		"""

		chunks = [None] * len_workers
		chunk_index = 0
		mutantsForOp = [None]
		
		operatorsList = operators.operatorsSet() # return a list of all mutant operators
		
		for op in operatorsList:
			
			#Check if there are mutants related to that operator
			if op in mutant_set.keys():
				mutantsForOp = mutant_set[op] #Creates a list for all mutants of the Operator 'op'

				#For each mutant in the list of mutants of 'op'
				for mutant in mutantsForOp:

					#To avoid the error of concatenate NoneType + List, first check if the element is None or not.

					if chunks[chunk_index]:   #Already have something, keep add information to that chunk
						chunks[chunk_index] = chunks[chunk_index] + [mutant] #create a chunk with the mutant and the test_set
					
					else: #There are nothing in the index of the list.  
						chunks[chunk_index] = [test_set, mutant]  #Each element -> [{tcaseID:[inputs]}, mutantID]

					#Increase the chunk index
					chunk_index = (chunk_index+1) % len_workers #increase the chunk_index

		#Get the dictionary of workers registred, then get just the list with the address of all  registred workers
		workers = self.waiting_list[constants.WORKER].values()

		for chunk,worker in zip(chunks,workers):
			worker = worker[0] #The address is inside of a list, pop just to remove the list 
			self.send_msg_worker(worker, constants.SERIALIZE, chunk)
			  


	"""
		Distribute Test Cases Algorithm
	"""
	def dtc(self,mutant_set,test_set,len_workers):

		"""
		Args:
			mutant_set  = dict with all mutant and their operators -> {op:[mut_id]} -> u-ORSN: [528, 529, 530], u-OCNG: [323, 324, 325]
			test_set    = dict with all the test cases and a id -> {id:[inputs]} -> 10: [7, 24, 9, 24, 1963]
			len_workers = number of processors avaliable
		"""

		#The number of chunks is always the same of workers
		chunks = [None] * len_workers
		chunk_index = 0

		#Take the values of the dict of mutants and convert into a list with all mutants id -> [1,2,3,4, ... ]
		mutants_list = list(chain(*mutant_set.values()))

		test_cases = test_set.values()

		#For every worker expected
		for worker in range(len_workers):

			#If there is a testcase to send for that worker..
			if worker < len(test_cases):

				chunks[worker] = [mutants_list,test_cases[chunk_index]] #create a chunk with the testcase

			else:
				chunks[worker] = [mutants_list,[]] #Create a chunk without testcase


			chunk_index = (chunk_index+1) % len_workers   #Increase the chunk index


		#Get the dictionary of workers registred, then get just the list with the address of all  registred workers
		workers = self.waiting_list[constants.WORKER].values()
		i = 1
		for chunk,worker in zip(chunks,workers):
			print 'interation: ',i
			print 'mutants: ', len(chunk[0])
			print 'testcase: ',chunk[1]
			worker = worker[0] #The address is inside of a list, get index 0 just to remove the brackets of list 
			self.send_msg_worker(worker, constants.SERIALIZE, chunk)




	"""
		Given Mutants On Demand Algorithm
	"""
	def gmod(self,mutant_set, test_set):

		"""
		Args:
			mutant_set    = dict with all mutant and their operators -> {op:[mut_id]} -> u-ORSN: [528, 529, 530], u-OCNG: [323, 324, 325]
			test_set      = dict with all the test cases and a id -> {id:[inputs]} -> 10: [7, 24, 9, 24, 1963]
		"""
		
		#Condition for worker ask for chunks
		stop = False

		#Take the values of the dict of mutants and convert into a list with all mutants id -> [1,2,3,4, ... ]
		mutants_list = list(chain(*mutant_set.values()))
		
		#The number of chunks is equals to the number of mutants
		chunks = [None] * len(mutants_list)
		chunk_index = 0

		for mutant in mutants_list:
			chunks[chunk_index] = [mutant,test_set]
			chunk_index = chunk_index + 1

		#Number of chunks processed
		chunkProcessedIndex = 0

		if verbose: print "I: It's a dynamic approach. Will wait for requests from workers to send the data.."

		while (chunkProcessedIndex < chunk_index):
						
			#Wait for worker
			worker,data = self.recive_request()

			#Send the msg to worker
			self.send_msg_worker(worker, constants.SERIALIZE, chunks[chunkProcessedIndex])

			#process one chunk
			chunkProcessedIndex = chunkProcessedIndex + 1
			

	"""
		Give Test Cases On Demand Algorithm
	"""
	def gtcod(self,mutant_set, test_set):
		
		"""
		Args:
			mutant_set    = list of all mutant
			test_set      = list with all the test cases
		"""

		#Take the values of the dict of mutants and convert into a list with all mutants id -> [1,2,3,4, ... ]
		tcase_list = test_set.values()

		#Convert the mutant dict into a list
		mutants_list = list(chain(*mutant_set.values()))

		#The number of chunks is equals to the number of test cases
		chunks = [None] * len(tcase_list)
		chunk_index = 0

		#For each tcase
		for testCase in tcase_list:

			#Create a chunk with all mutants and one tcase
			chunks[chunk_index] = [mutants_list,testCase]
			chunk_index = chunk_index + 1 #Increase the number of chunks

		#Define the number of processed chunks
		chunkProcessedIndex = 0

		#While the number of processed chunks is lower then the number of chunks..
		while (chunkProcessedIndex < chunk_index):

			#Get a avaliable worker
			worker,data = self.recive_request()

			self.send_msg_worker(worker, constants.SERIALIZE, chunks[chunkProcessedIndex]) #Send the data
			chunkProcessedIndex = chunkProcessedIndex + 1 #Increase the number of processed chunks



	"""
		Parallel Execution with Dynamic Ranking and Ordering Algorithm
	"""
	def pedro(self,mutant_set, test_set, len_workers, n):

		"""
		Args:
			mutant_set  = list with all mutant operators
			test_set    = a dictionary with all the test cases
			len_workers = number of processors avaliable
			n           = integer fixed by the user that determines the number of chunks to be executed in each phase
 		"""
	
		#First Phase of the execution
		mutant_index = 0

		#Number of the first chunkss is equals to the number of workers registred
		chunks1 = [None] * len_workers

		#Take the values of the dict of mutants and convert into a list with all mutants id -> [1,2,3,4, ... ]
		mutants_list = list(chain(*mutant_set.values()))

		#Chunk size is equals to the max beetwen the variables described
		chunkSize = max(len(mutants_list) / (len_workers * n) , 1)

		#This loop will create the first set off chunks
		for i in xrange(len(chunks1)):
			for j in xrange(chunkSize):
				if chunks1[i]:
					chunks1[i]   = chunks1[i] + [mutants_list[mutant_index]] 

				else:
					chunks1[i] = [test_set, mutants_list[mutant_index]]
				
				#Always increment the chunk 
				mutant_index = mutant_index + 1

		#Get the dictionary of workers registred, then get just the list with the address of all  registred workers
		workers = self.waiting_list[constants.WORKER].values()	

		#Send each chunk1 for each worker. The number of chunks1 and workers are always the same.
		for chunk,worker in zip(chunks1,workers):
			worker = worker[0] #The address is inside of a list, pop just to remove the list 
			self.send_msg_worker(worker, constants.SERIALIZE, chunk)

		#Second Phase of the execution

		# This loop will send data dynamically, basead on the results of the first phase
		while (mutant_index<len(mutants_list)):

			worker,data = self.recive_request() #Get the first avaliable worker

			#calcule the size of the chunk that will be sended to the worker
			chunkSize = max((len(mutants_list)-mutant_index)/(len_workers * n),1)
			chunk = None

			#create the chunk
			for i in xrange(chunkSize):
				
				if chunk:
					chunk = chunk + [mutants_list[mutant_index]] 
					mutant_index = mutant_index + 1  #increase the mutant index

				else:
					chunk = [test_set, mutants_list[mutant_index]]  
					mutant_index = mutant_index + 1  #increase the mutant index

			#send the chunk to the worker
			self.send_msg_worker(worker, constants.SERIALIZE,chunk)
