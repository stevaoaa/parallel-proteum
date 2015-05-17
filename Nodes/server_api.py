#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import zmq

from Proteum.Util import constants
from Proteum.Util import serialize_util

verbose = True

class Server():

	"""
		Args:
			scheduler_adr = A string with the end point of scheduler
			context       = ZMQ context
			server_sock   = A ZMQ socket to comunicate with 
			poller        = ZMQ poller
			verbose       = Defines if the log information is active
	"""

	scheduler_adr = None
	context       = None
	server_sock   = None
	poller        = None
	program_name  = None



	"""
		Constructor: Inicialize the server_sock state
	"""
	def __init__(self,scheduler_adr,program_name):

		self.scheduler_adr = scheduler_adr
		self.context = zmq.Context()
		self.poller = zmq.Poller()

		self.program_name = program_name

		self.connect_to_scheduler()



	"""
		This method is used to connect or reconect to the scheduler
	"""
	def connect_to_scheduler(self):

		#Creats a ZQM worker socket (Dealer type) and connect it at the scheduler		
		self.server_sock = self.context.socket(zmq.DEALER)
		self.server_sock.linger  = 0

		self.server_sock.connect(self.scheduler_adr)

		#Register the worker_sock for I/O monitoring.
		self.poller.register(self.server_sock, zmq.POLLIN)

		if verbose: print "I: Connecting to SCHEDULER at %s" % self.scheduler_adr

		# At this point sends a empty message "[]" to the scheduler just to notify that the server is ready to start the job 


	"""
		Send a request to scheduler and get some response
	"""
	def send_to_scheduler(self,command, serialized, msg=None):

		"""
		Args:
			command  = Kind of information sended (ready, request, reply, disconnect "see constants.py")
			serialize = specifies if the data need to be serialized			
			msg      = the data 
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
					msg[3] = The data 
			"""

			#Before send the message need to serialize it
			msg = serialize_util.compress(msg) 

		msg = ['',constants.SERVER, command, serialized, self.program_name, msg]

		if verbose: print "I: Send request to the scheduler at: %s. Type of command: %s " % (self.scheduler_adr,command.upper() )

		#Send request to the scheduler. Already knows where to send the message because of the line 54.		
		self.server_sock.send_multipart(msg)


	"""
		Recive a response of some request
	"""		
	def recive_response(self, timeout = None):

		print "I: Waitting for a response from SCHEDULER.."
		
		#Wait forever util the scheduler process and send back the response
		try:
			items = self.poller.poll(timeout)
		except KeyboardInterrupt:

			if verbose: print "I: The execution was interrupted by keyboard! Restart the process.."
			sys.exit(1)

		if items:

			#Revice a message as a list of frame objects
			msg = self.server_sock.recv_multipart()
			
			serialize = msg.pop(0)

			#Remove message from the list
			msg = msg.pop(0)

			#If its true, need decompress the data
			if(serialize == constants.SERIALIZE):
				msg = serialize_util.decompress(msg)

			if (len(msg) < 1):
				if verbose: print "W: There is a error in the send function. Reciving a msg with some erros..."

			if verbose: print "I: Recived the reply from SCHEDULER"

		else:
			if verbose: print "W: Error! Leaving... Please, restart the service.."
			sys.exit(1)

		return msg


	"""
		ZQM context destroy
	"""
	def destroy(self):
		if verbose: print "I: Closing the socket and finishing the execution.."
		self.context.destroy()