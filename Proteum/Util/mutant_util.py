#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
The method recives a vector with mutants 'Numbers' and converts to a string suitable to be used
In the exemuta module
SAMPLE:
list = ['4','8','45','57','61','66','254']
string = list_string(mutantVector)
statment = 'exemuta -select -x  %s ' + program % (string)
Expected statment: exemuta -select -x "4 8 45 57 61 66 254" program
"""
def list_string(list):
    string = str(list)
    string = string[1:-1] #removing the '[]' of the vector from the string
    string = "\""+string+"\""
    string = string.replace(',','') #removing ',' from the string
    string = string.replace('\'','') #removing ',' from the string
    return string



"""
Same as above, but don't insert double quotes into the string
SAMPLE:
list = ['-u-CCDL  1.0 ', '-u-OODL  1.0 ', '-u-SSDL  1.0 ']
string = list_string2(list)
print string --> "-u-CCDL  1.0 -u-OODL  1.0  -u-SSDL  1.0"
"""
def list_string2(list):
    string = str(list)
    string = string[1:-1] #removing the '[]' of the vector from the string
    string = string.replace(',','') #removing ',' from the string
    string = string.replace('\'','') #removing ',' from the string
    return string



"""
Used to define how retrive informations from de module "muta -l"
Require the use of one routine for capturing the shell output in a  variable.
Se the sample at the end of file
"""
def get_mutant(shell_output):

    start  = shell_output.find('#')
    start2 = shell_output.find('Operator:')
    start3 = shell_output.find('Status')
    start4 = shell_output.find('Causa')

    if start == -1:
        return None,0,0,0,0

    start_op     = shell_output.find('(', start2)  #begin of operator
    start_mutant = shell_output.find('# ', start)   #begin of mutant
    start_status = shell_output.find(' ',start3)   #begin of status
    start_causa  = shell_output.find(' - ',start4) #begin of causa mortis

    end_op     = shell_output.find('\n', start_op)     #end position for operator
    end_mutant = shell_output.find('\n', start_mutant) #end position for mutant
    end_status = shell_output.find('\n', start_status) #end position for status
    end_causa  = shell_output.find('\n', start_causa)  #end position for causa mortis

    mutant       = shell_output[start_mutant+1:end_mutant].strip() #retriving the mutant information
    operator     = shell_output[start_op+1:end_op-1].strip()       #retriving the operator information
    status       = shell_output[start_status+1:end_status].strip() #retriving the status information
    causa_mortis = shell_output[start_causa+3:end_causa].strip()   #retriving the causa mortis information

    return mutant,operator,status,causa_mortis, end_op



"""
Used to retrive all the information existent on "shellOutput" which was defined on "get_mutant"
In this case, return a hashtable where: key = Mutant Operator; Value = Mutants genereted by the operator
"""
def get_all_mutants(shell_output):

    mutants_status      = {} #This keeps a dictionary with some information for every mutant where: Key = Mutant index and Value contains some informations for that mutant
    mutants_by_operator = {} #This keeps a dictionary like where: Key = Operator and Value = List of mutants for that operator

    while True:

        mutant, operator, status, causa_mortis, end_op = get_mutant(shell_output)

        if mutant:

            mutants_status[mutant] = (status,causa_mortis,operator) #Populate the dict mutants_status

            if operator in mutants_by_operator:
                mutants_by_operator[operator].append(mutant) #If the Key 'Operator' already exists, add the mutant at the value of this key
            else:
                mutants_by_operator[operator] = [mutant] #Else, create a key and add the mutant to the vector of mutants relateds to that operator

            shell_output = shell_output[end_op:] #Refresh the content of the shellOutput

        else:
            break #When mutant is None the loop finish the read  of shell_output content

    return mutants_by_operator,mutants_status



"""
Calculate the mutant score.
mutants_list = List with all mutants
equivalents_list = List with all equivalent mutants
dead_list = List with all dead mutants
"""
def mutation_score(mutants_list, equivalents_list, dead_list):
    score = len(dead_list) / float((len(mutants_list) - len(equivalents_list)))
    return score


"""
    Yield successive n-sized chunks from l.
"""
def chunk_list(a, n):
    k, m = len(a) / n, len(a) % n
    return (a[ i * k + min(i, m):(i+1) * k + min(i + 1, m)] for i in xrange(n))