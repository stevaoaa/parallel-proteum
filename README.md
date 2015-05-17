Parallel Proteum
==================

This project presents a tool that aims to enable the application of mutation test in parallel.

In order to execute parallel proteum, first you must have a functional sequential version of Proteum.


How to compile Proteum
-----------------------

In the base directory there is a primitive makefile which will do the job.
Improvements to the compilation and installation process are wellcome.

Source code: <https://drive.google.com/file/d/0B4n1OQ2HWrYVeVlTLUJfbFUyX1U/view?usp=sharing>

Currently Proteum only compiles on linux, as far as I know. We didn't try on other
OS.


How to install
---------------

After compiling the executables and scripts will be in the LINUX/bin directory.
Just copy those file where you want and it is ready to use.

Bin compiled: <https://drive.google.com/file/d/0B4n1OQ2HWrYVZGtqYmowTklNOTg/view?usp=sharing>


How to run 
-------------

Proteum requires GCC to be installed. To use its GUI it is also necessary 
TCL/TK.

Suposing the executable files are in directory /usr/bin/proteum, run

> export PROTEUMIMHOME=/usr/bin/proteum

> export PATH=$PROTEUMIMHOME:$PATH

> proteumim

Proteum can also be run by a command line.

How execute Parallel Proteum
-----------------------------

First of all you will need install PYZMQ a extra Python Lib:

> easy_install pyzmq

or

> pip install pyzmq

Extra information can be found: http://zeromq.org/bindings:python

After that you are ready to run the scrpit.

Parallel Proteum can be performed in localhost or in a set of computers connected by a IP network.

There are 3 types os computers:

Server
------

The server is the machine responsible for controlling the mutation test execution process. He is responsible for defining the group of mutants and the set of test cases that will be used.

You should put the folder of program that you want test inside the folder /Experiments/Programs/

The folder of the program under testing should contains the following list of files:

* program.c     - Source code of the program
* compile.txt   - Command used in GCC to compile the program
* functions.txt - List of functions that you want to test. (If this file is empty than Proteum will mutate all functions including the main)
* testset.txt   - List with all test that you want to execute in the process.

Check one of the directories inside  /Experiments/Programs/ to see a pratical example.

To execute the server just go to a terminal and type:

> python server.py scheduler_ip


Scheduler
---------

The Scheduler is the machine responsible for distributing work portions (mutants and test cases) between the Workers.




After that, just run:

> python scheduler.py algorithm 

Algorithms avaliable:  ['dmbo', 'dtc', 'gmod', 'gtcod', 'pedro']

Note: Scheduler machine doesn't need of a Proteum version installed


Workers
-------

Workers are responsible for performing the execution of the mutants with the set of test cases provided. In general, each worker computer behaves as a sequential version of the Proteum tool.

After that, just run the command:

> python worker.py scheduler_ip

