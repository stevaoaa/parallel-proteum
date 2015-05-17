#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	Here are defined some userfull constants and commands
"""

SERIALIZE = 'serialize' #Create this constants because we can't send over the wire a boolean to informe if the data is serialized or not
NSERIALIZE = 'nserialize'

""" A list that contains the commands avaliables:
		
		READY      = This command indicates that the worker is ready to do some stuff 
		REQUEST    = This command indicates that the worker is avaliable to recive some job
		REPLY      = This command indicates that information is a reply of some request
		DISCONNECT = This command indicates the end of execution and that worker is closing the conection
"""
commands = [None, "READY", "REQUEST", "REPLY", "DISCONNECT", "SYNCHRONIZE"]

READY      = "READY"
REQUEST    = "REQUEST"
REPLY      = "REPLY"
DISCONNECT = "DISCONNECT"
SYNCHRONIZE = "SYNCHRONIZE"


""" A list that contains the avaliable machines:

		server    = Controls the process
		scheduler = Workload balancer
		worker    = Workload processer 
"""
machines = [None, 'server', 'scheduler', 'worker']

WORKER    = 'worker'
SERVER    = 'server'
SCHEDULER = 'scheduler'


"""
	A list that contains the possible status of a mutant
"""
status = ['alive', 'dead', 'anomalous', 'equivalent', 'inactive']

ALIVE      = 'Alive'
DEAD       = 'Dead'
ANOMALOUS  = 'Anomalous'
EQUIVALENT = 'Equivalent'
INACTIVE   = 'Inactive'


""" A list that contains the name of workload algorithms

		dmbo   = Distribute mutants between operators Algorithm
		dtc    = Distribute Test Cases Algorithm
		gmod   = Given Mutants On Demand Algorithm
		gtcod  = Give Test Cases On Demand Algorithm
		pedro  = Parallel Execution with Dynamic Ranking and Ordering Algorithm
"""
algorithms = ['dmbo', 'dtc', 'gmod', 'gtcod', 'pedro']

DMBO  = 'dmbo'
DTC   = 'dtc'
GMOD  = 'gmod'
GTCOD = 'gtcod'
PEDRO = 'pedro'