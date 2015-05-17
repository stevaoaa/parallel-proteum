import string

usual_Operators    = ["u-Cccr", "u-CCDL", "u-Ccsr", "u-CRCR", "u-OAAA", "u-OAAN", "u-OABA", "u-OABN", "u-OAEA", "u-OALN", "u-OARN", "u-OASA", "u-OASN", "u-OBAA", "u-OBAN", "u-OBBA", "u-OBBN", "u-OBEA", "u-OBLN", "u-OBNG", "u-OBRN", "u-OBSA", "u-OBSN", "u-OCNG", "u-OCOR", "u-OEAA", "u-OEBA", "u-OESA", "u-Oido", "u-OIPM", "u-OLAN", "u-OLBN", "u-OLLN", "u-OLNG", "u-OLRN", "u-OLSN", "u-OODL", "u-ORAN", "u-ORBN", "u-ORLN", "u-ORRN", "u-ORSN", "u-OSAA", "u-OSAN", "u-OSBA", "u-OSBN", "u-OSEA", "u-OSLN", "u-OSRN", "u-OSSA", "u-OSSN", "u-SBRC", "u-SBRn", "u-SCRB", "u-SCRn", "u-SDWD", "u-SGLR", "u-SMTC", "u-SMTT", "u-SMVB", "u-SRSR", "u-SSDL", "u-SSWM", "u-STRI", "u-STRP", "u-SWDD", "u-VDTR", "u-VGAR", "u-VGPR", "u-VGSR", "u-VGTR", "u-VLAR", "u-VLPR", "u-VLSR", "u-VLTR", "u-VSCR", "u-VTWD", "u-VVDL", "SSDL+ORRN", "VLAR+VGAR", "VLPR+VGPR", "VLSR+VGSR", "VLTR+VGTR", "Random 10\%" ]
deletion_Operators = ["u-CCDL", "u-OODL", "u-SSDL", "u-VVDL", "CCDL+SSDL", "CCDL+VVDL", "OODL+SSDL", "SSDL+VVDL","CCDL+SSDL+VVDL", "Random 1\%", "Random 2\%", "Random 3\%", "Random 4\%", "Random 5\%", "Random 10\%", "Random 15\%", "Random 20\%" ]

operatorsList = usual_Operators + deletion_Operators


def randomNumber(s):
    i = s.find("Random") + 7
    j = s.find("\%")
    ns = s[i:j]
    x = float(ns) / 100.0
    return "%4.2f" % x


def opToString(op):
    if (op.find("Random") >= 0):
	return "-global " +  randomNumber(op) + " "
    i = op.find("+")
    s = " 100 "
    if (i >= 0):
	ret = ""
	while (i >= 0 ):
	    op1 = op[0:i]
	    op = op[i+1:]
	    ret += "-u-" + op1 + s
	    i = op.find("+")
	ret += "-u-" + op + s
	return ret
    else:
	return "-" + op + s

def setToString(xset):
    s = ""
    for x in xset:
	s += opToString(x)
    return s


def operatorsSet():
    return set(operatorsList)



if __name__=="__main__":                       # If this script is run as a program:
   print operatorsList
   print setToString(operatorsSet)

