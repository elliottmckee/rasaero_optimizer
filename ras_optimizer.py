import os
import re
import sys 
import time
import json
import warnings
import itertools
import xml.etree.ElementTree as ET

import numpy as np
import pyautogui
import pyperclip
from matplotlib import pyplot as plt



def parse_cdx1(filename):

    tree = ET.parse(filename)
    root = tree.getroot()

    print(f'Reading in: {filename}... \n')
    # tree.write(sys.stdout, encoding='unicode', xml_declaration=True)

    return tree, root


def cdx1_subs(infile, outfile, subs):
    # inputs a dictionary of key-value pairs, uses that to overwrite/modify an existing CDX1 file
    tree, root = parse_cdx1(infile)
    
    # apply subs
    for property, value in subs.items():
        element = root.find(property)
        if element is not None:
            element.text = str(value)
            
    tree.write(outfile, encoding='unicode', xml_declaration=False)




def cdx1_sweep(infile, outfile, sweep_dict, rules=[], mode="zip"):
    """
    runs a sweep of overrides through RAS, given an XML file and dictionary of mods to apply. 
    
    args:
        infile (str): path to the original XML file
        outfile (str): path to write modified XML file
        sweep_dict (dict): dict where keys are XML properties, values are lists of values to sweep
        rules (list): list of general "rules" to apply to every case after the overrides have been rendered.
        mode (str): "zip" for paired iteration, "product" for combinations

    outputs:
        results: list of max altitude data
        run_values: numpy array of input values used for each run
    """

    results = []
    run_values = []

    keys, values = zip(*sweep_dict.items())  # Extract keys and value lists
    sweep_iter = zip(*values) if mode == "zip" else itertools.product(*values)
    sweep_iter_list = list(zip(*values) if mode == "zip" else itertools.product(*values))

    print(f'\n\t NUMBER OF RUNS COMMENCING: {len(sweep_iter_list)}')
    print(f'\t Estimated runtime: ~{len(sweep_iter_list)*5} seconds\n')

    for i, value_combo in enumerate(sweep_iter):
        run_values.append(list(value_combo))
        overrides = dict(zip(keys, value_combo))

        for rule in rules:
            # i could overengineer a better way to do this, but this is a fucking autogui script
            # see examples for usage
            exec(rule) 
        
        cdx1_subs(infile, outfile, overrides)
        
        print(f"Running: {outfile} with overrides {overrides}...")
        results.append(open_and_run_RAS(outfile, treat_marginal_stability_as_fail=False))
        
    return results, np.array(run_values)



# CONFIG - POINTER LOCATION OFFSETS FOR NAVIGATION
FILE_OFFSET             = [20, 40]  # location of File button in main-window-coordinates
OPEN_OFFSET_REL         = [0, 45]   # relative location offset when file->open
FLIGHT_OFFSET           = [500, 65] # location of Flight Simulation button in main-window-coordinates
VD_BUTTON_OFFSET        = [0, 30]   # offset between FlightSim - ViewData top label and actual button
RCLICK_CLOSE_OFFSET_REL = [10, 125] # relative location offset when right-click-closing a window
DOWN_RIGHT_NUDGE        = [10,10]   # just a nudge down and right

# CONFIG - DELAYS
SLEEP_DEBUG         = 0.0   # set to non-zero to see movements for debugging
SLEEP_WINDOW_OPEN   = 0.7;  # delay added for opening new windows, which takes a bit sometimes
SLEEP_RUN_SIM       = 0.4;  # delay added to allow sim to run fully


def open_and_run_RAS(filename, pull_all_data = False, treat_marginal_stability_as_fail = False):

    time.sleep(0.1) # additional sleep for additional "robustness" between closing of one run and start of another

    #~~~~~~~~~~~~~~~~~~~~~~~ MAIN WINDOW ~~~~~~~~~~~~~~~~~~~~~#

    # Find location of open rasWindow (rW)
    rW_x, rW_y, rW_w, rW_h = pyautogui.locateOnScreen('resource/MAIN_TOOLBAR.PNG', confidence=0.7)

    # FILE
    pyautogui.moveTo(rW_x+FILE_OFFSET[0], rW_y+FILE_OFFSET[1], duration=SLEEP_DEBUG)
    pyautogui.click()

    # OPEN
    pyautogui.moveRel(OPEN_OFFSET_REL[0], OPEN_OFFSET_REL[1], duration=SLEEP_DEBUG)
    pyautogui.click()
    time.sleep(SLEEP_WINDOW_OPEN)
    pyautogui.write(filename)
    pyautogui.press('enter')

    # OPEN FLIGHT SIMULATION
    pyautogui.moveTo(rW_x+FLIGHT_OFFSET[0], rW_y+FLIGHT_OFFSET[1], duration=SLEEP_DEBUG)
    pyautogui.click()
    time.sleep(SLEEP_WINDOW_OPEN)

    
    #~~~~~~~~~~~~~~~~~~~~~~~ FLIGHT SIMULATION WINDOW ~~~~~~~~~~~~~~~~~~~~~#

    # Find location of flightsimulationWindow (fsW)
    fsW_x, fsW_y, fsW_w, fsW_h = pyautogui.locateOnScreen('resource/FLIGHT_TOOLBAR.PNG', confidence=0.7)

    # We need to find the viewData button, since this spreadsheet view is resizable :(
    # this currently looks for the top label of the view data column, then goes down to the first button
    vD_x, vD_y = pyautogui.locateCenterOnScreen('resource/FLIGHT_VIEWDATA.PNG', confidence=0.7)
    pyautogui.moveTo(vD_x+VD_BUTTON_OFFSET[0], vD_y+VD_BUTTON_OFFSET[1], duration=SLEEP_DEBUG)

    # Run simulation
    pyautogui.rightClick()
    pyautogui.moveRel(DOWN_RIGHT_NUDGE[0], DOWN_RIGHT_NUDGE[1], duration=SLEEP_DEBUG)
    pyautogui.click()
    time.sleep(SLEEP_RUN_SIM)
    

    # ~~~~~~~~~~~~~~~~~~~~~~~ ERROR HANDLING ~~~~~~~~~~~~~~~~~~~~~#
    
    # CHECK FOR UNSTABLE ~~~ERROR~~~
    try: 
        # look for unstable window
        ue_x, ue_y = pyautogui.locateCenterOnScreen('resource/FLIGHT_UNSTABLE_ERR.PNG', confidence=0.8)

        # if exists, close windows, return null
        pyautogui.rightClick(ue_x, ue_y)
        pyautogui.moveRel(RCLICK_CLOSE_OFFSET_REL[0], RCLICK_CLOSE_OFFSET_REL[1], duration=SLEEP_DEBUG) 
        pyautogui.click()

        warnings.warn('This case was unstable!')
        close_flight_sim_window(fsW_x, fsW_y)
        
        return np.nan;
    
    except pyautogui.ImageNotFoundException: 
        # if no window, continue nominally
        pass


    # CHECK FOR MARGINAL STABILITY ~~~WARNING~~~
    try: 
        # look for unstable window
        ms_x, ms_y = pyautogui.locateCenterOnScreen('resource/FLIGHT_MARGINAL_STAB.PNG', confidence=0.8)

        # if exists, close window
        pyautogui.rightClick(ms_x, ms_y)
        pyautogui.moveRel(RCLICK_CLOSE_OFFSET_REL[0], RCLICK_CLOSE_OFFSET_REL[1], duration=SLEEP_DEBUG) 
        pyautogui.click()

        if treat_marginal_stability_as_fail:
            # soft.com - close out flight sim window and return null
            close_flight_sim_window(fsW_x, fsW_y)
            return np.nan;

        else:
            # DEFAULT - in this household we let that shit ride - warn but continue
            warnings.warn('Marginal stability warning encountered!')
            pass
    
    except pyautogui.ImageNotFoundException: 
        # if no window, continue nominally
        pass


    # ~~~~~~~~~~~~~~~~~~~~~~~ EXTRACT DATA  ~~~~~~~~~~~~~~~~~~~~~#
    
    if pull_all_data:
        raise Exception('NOT IMPLEMENTED YET')
    
    else: # just pull data from max altitude column

        # Find location of maxAlt (mA) column, since this spreadsheet view is resizable :(
        mA_x, mA_y = pyautogui.locateCenterOnScreen('resource/FLIGHT_MAXALT.PNG', confidence=0.7)

        # move over maxAlt result
        MA_BUTTON_OFFSET = [0, 30] # offset between label and button
        pyautogui.moveTo(mA_x+MA_BUTTON_OFFSET[0], mA_y+MA_BUTTON_OFFSET[1], duration=SLEEP_DEBUG)

        # copy data to clipboard
        pyautogui.click()
        pyautogui.hotkey('ctrl', 'c')
        result = float(pyperclip.paste().replace(",", ""))
        print('Max Alt: ', result)

    close_flight_sim_window(fsW_x, fsW_y)

    return result


def close_flight_sim_window(fsW_x, fsW_y):
    # just does the two-step process of closing the window, and hitting the confirmation prompt 
    
    CLOSECONFIRM_OFFSET_REL = [125, 20];# this currently targets "NO", but can use to change if need to

    # i really gamered up by finding out you can right click the top bar to close the window
    pyautogui.rightClick(fsW_x+DOWN_RIGHT_NUDGE[0], fsW_y+DOWN_RIGHT_NUDGE[1]) # right click top bar
    pyautogui.moveRel(RCLICK_CLOSE_OFFSET_REL[0], RCLICK_CLOSE_OFFSET_REL[1], duration=SLEEP_DEBUG) 
    pyautogui.click()
    time.sleep(SLEEP_WINDOW_OPEN)

    # close closeConfirm (cC, unfort need to find window)
    cC_x, cC_y, _, _ = pyautogui.locateOnScreen('resource/FLIGHT_CLOSECONFIRM.PNG', confidence=0.7)
    pyautogui.moveTo(cC_x+CLOSECONFIRM_OFFSET_REL[0], cC_y+CLOSECONFIRM_OFFSET_REL[1])
    pyautogui.click()




if __name__ == '__main__':

    ### ~~~~~~~ INPUTS ~~~~~~~ ###

    # template cdx1 rocket file
    cdx1_template = 'resource/EXAMPLE_Loki.CDX1'

    # define substitutions/iterations 
    sweep_dict = {".//Fin/Span": [1.5, 1.7, 2.0, 2.5, 3.0]} # THESE CASES COVERS ALL RAS STABILITY WARNING/ERROR SCENARIOS

    # temp file to write cdx1 files to
    temp_file = os.path.join(os.getcwd(), 'TEMPFILE.CDX1')

    ### ~~~~~~~~~~ MAIN ~~~~~~~~~~~~ ###

    print('\n Waiting a second to allow user to make RAS visible if needed...\n')
    time.sleep(2) 
    print('Beginning RAS iteration...')

    # ~ main call ~
    # this is a helper for performing sweeps and returning results, 
    # but you can also make your own logic and talk to open_and_run_RAS() directly as needed 
    results, run_values = cdx1_sweep(cdx1_template, temp_file, sweep_dict, mode="product")

    # print results to screen
    print('Run Values: \n', run_values)
    print('Results: \n', results)

    ### ~~~~~~~~~~ PLOTTING ~~~~~~~~~~~~ ###
    
    # scatter plot
    keylist = list(sweep_dict.keys())
    scatter = plt.plot(run_values[:,0], results, linestyle='-', marker='o')
    plt.xlabel(keylist[0])
    plt.ylabel("Max Alt")
    plt.title("Example Sweep Results")
    plt.grid()
    plt.show()
