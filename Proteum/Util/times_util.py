import time

"""
    This python file contains some methods used in a course to mesure the time execution of another methods 
"""


"""
    Takes a function as args. The main point is mesure the execution time of some function. It's used as a decorator
    Ex: @timeit foo() -> Will measure the execution time of foo()
"""
def timeit(f):

    def timed(*args, **kw):

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        
        et = te-ts #execution time
        
        #print 'func:%r args:[%r, %r] took: %2.4f sec' % \
          #(f.__name__, args, kw, te-ts)
        
        return result

    return timed