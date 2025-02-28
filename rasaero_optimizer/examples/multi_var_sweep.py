# example driver script for a multi-variate sweep
import itertools
import os
import time

import numpy as np
from matplotlib import pyplot as plt

from ..rasaero_optimizer import cdx1_sweep

RSRC_PATH  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resource')


if __name__ == '__main__':

    ### ~~~~~~~ INPUTS ~~~~~~~ ###

    cdx1_template = os.path.join(RSRC_PATH, 'EXAMPLE_Loki.CDX1')

    # Fin variables we can play with (copied from example CDX1 file)
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

    # sweep matrix
    sweep_dict = {  ".//Fin/Chord":         np.linspace(5, 10, 3),
                    ".//Fin/SweepDistance": np.linspace(2, 7, 3),
    }

    # sweep_dict = {  ".//Fin/Chord":         np.linspace(5, 10, 3),
    #                 ".//Fin/TipChord":      np.linspace(0.5, 5, 3),
    #                 ".//Fin/Span":          np.linspace(1.5, 3, 3),
    #                 ".//Fin/SweepDistance": np.linspace(2, 7, 3),
    # }

    # additional rules to apply
    # these are called with a really dumb/simple exec() call from within cdx1_sweep(), 
    # which is why we need the extra overrides[] jargon, but if you're this far, i think you've got this, i believe in you
    rules = [r"overrides['.//Fin/Location'] = overrides['.//Fin/Chord'] + 1.0"] # force fin to be 1" from base of tube

    # temp file
    temp_file = os.path.join(os.getcwd(), 'TEMPFILE.CDX1')

    ### ~~~~~~~~~~ MAIN ~~~~~~~~~~~~ ###

    print('\n Waiting a second to allow user to make RAS visible...\n')
    time.sleep(2) 
    print('Beginning RAS iteration...')

    results, run_values = cdx1_sweep(cdx1_template, temp_file, sweep_dict, rules=rules, mode="product")

    print('Run Values: \n', run_values)
    print('Results: \n', results)

    ### ~~~~~~~~~~ PLOTTING ~~~~~~~~~~~~ ###

    # scatter
    keylist = list(sweep_dict.keys())
    scatter = plt.scatter(run_values[:,0], run_values[:,1], c=results, cmap="viridis")
    plt.colorbar(label="Max Alt")
    plt.xlabel(keylist[0])
    plt.ylabel(keylist[1])
    plt.title("2-variable sweep")

    # filled contour
    x_unique = np.unique(run_values[:,0])
    y_unique = np.unique(run_values[:,1])
    X, Y = np.meshgrid(x_unique, y_unique)
    Z = np.array(results).reshape(len(x_unique), len(y_unique))

    plt.figure()
    contour = plt.contourf(X, Y, Z.T, levels=20, cmap="viridis")
    plt.scatter(run_values[:,0], run_values[:,1], c=results, cmap="viridis", edgecolors='k')
    plt.colorbar(label="Max Alt")
    plt.xlabel(keylist[0])
    plt.ylabel(keylist[1])
    plt.title("2-variable sweep")

    plt.show()

    










 







    








