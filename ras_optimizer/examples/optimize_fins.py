# example driver script for a multi-variate sweep
import itertools
import os
import time
import tempfile

import scipy
import numpy as np
from matplotlib import pyplot as plt

from ras_optimizer.ras_optimizer import cdx1_sweep, open_and_run_RAS, parse_cdx1, cdx1_subs

RSRC_PATH  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resource')


def optimize_fun(x, cdx1_file='', vars=[]):
    # TODO: support rules

    # assemble scipy-values into "subs" dictionary
    subs = dict(zip(vars, x))
    print('Iteration values:', subs)

    # write temporary cdx1 file with subs
    temp_file = os.path.join(tempfile.gettempdir(), os.urandom(12).hex()+'.cdx1')
    # temp_file = tempfile.NamedTemporaryFile()
    cdx1_subs(cdx1_file, temp_file, subs)

    # get result
    result = open_and_run_RAS(temp_file, treat_marginal_stability_as_fail=False)
    result = -result # just flipping since scipy is trying to minimize

    # remove temp file
    os.remove(temp_file)

    # if nan result- punish
    if np.isnan(result):
        result = 0

    return result


def cdx1_optimize(cdx1_file, bounds):

    # variables to optimize over
    opt_vars = list(bounds.keys())
    print('Variables: ', opt_vars)

    # get initial guess from cdx1
    cdx1_tree, cdx1_root = parse_cdx1(cdx1_file)
    x0 = []
    for var in opt_vars:
        x0.append(float(cdx1_root.find(var).text))
    print('Initial Guess', x0)

    # wrapping as per minimize documentation
    wrapped_optimize_fun = lambda x: optimize_fun(x, cdx1_file=cdx1_file, vars=opt_vars)

    # optimize
    res = scipy.optimize.minimize(wrapped_optimize_fun, x0, method='Nelder-Mead', bounds = tuple(bounds.values()), tol=.1, options={'maxiter': 20, 'disp': True})
    # res = scipy.optimize.dual_annealing(wrapped_optimize_fun, tuple(bounds.values()), maxiter=100, initial_temp = 1000, x0=x0)

    return res



if __name__ == '__main__':

    ### ~~~~~~~ INPUTS ~~~~~~~ ###

    cdx1_template = os.path.join(RSRC_PATH, 'EXAMPLE_Loki.CDX1')

    # Fin variables to play with (copied from CDX1 file)
    # <Fin>
    #     <Count>3</Count>
    #     <Chord>9</Chord>
    #     <Span>3.937</Span>
    #     <SweepDistance>6</SweepDistance>
    #     <TipChord>3</TipChord>
    #     <Thickness>0.15</Thickness>
    #     <LERadius>0</LERadius>
    #     <Location>9.25</Location>
    #     <AirfoilSection>Hexagonal</AirfoilSection>
    #     <FX1>1</FX1>
    #     <FX3>1</FX3>
    # </Fin>

    # Dictionary of variables to play with, and bounds to remain between
    # bounds_dict = { ".//Fin/Chord":         (3,     10),
    #                 ".//Fin/TipChord":      (2,     10),
    #                 ".//Fin/Span":          (1.5,   5),
    #                 ".//Fin/SweepDistance": (2,     7),
    # }

    bounds_dict = { ".//Fin/TipChord":      (0.1,     6),
                    ".//Fin/Span":          (1.0,   4),
                    ".//Fin/SweepDistance": (2,     8),
    }

    # additional rules to apply
    # these are called with a really dumb/simple exec() call from within cdx1_sweep(), 
    # which is why we need the extra overrides[] jargon, but if you're this far, you've got this
    # rules = [r"overrides['.//Fin/Location'] = overrides['.//Fin/Chord'] + 1.0"] # force fin to be 1" from base of tube
    # THIS IS NOT SUPPORTED YET


    ### ~~~~~~~~~~ MAIN ~~~~~~~~~~~~ ###
    print('\n Waiting a second to allow user to make RAS visible...\n')
    time.sleep(2) 
    print('Beginning RAS iteration...')

    res = cdx1_optimize(cdx1_template, bounds_dict)
    print(res)



    










 







    








