
import sys, time
import xml.etree.ElementTree as ET

import pyautogui
import pyperclip
from matplotlib import pyplot as plt


def open_and_run_RAS(filename):
    # TODO:
    # Sometimes RAS puts underscores under these pictures, add redundancy?
    # Make more robust, making sure that the sim has completed before copy-pasting
    # I have done zero RAS-error handling

    # Give time for user to ALT+TAB
    # pyautogui.moveTo(500, 500, duration=1)

    # Open file
    x,y  = pyautogui.locateCenterOnScreen('resource/MAIN_File.PNG', confidence=0.7)
    pyautogui.click(x, y)
    x,y  = pyautogui.locateCenterOnScreen('resource/MAIN_Open.PNG', confidence=0.7)
    pyautogui.click(x, y)
    pyautogui.write(filename)
    pyautogui.press('enter')

    # Open FlightSim, run sim, view data
    time.sleep(0.8)
    x,y  = pyautogui.locateCenterOnScreen('resource/MAIN_Flight_Simulation.PNG', confidence=0.7)
    pyautogui.click(x, y)
    time.sleep(0.2)
    x,y  = pyautogui.locateCenterOnScreen('resource/FLIGHT_View_Data.PNG', confidence=0.7)
    pyautogui.rightClick(x, y)
    pyautogui.move(10, 10) # run sim
    pyautogui.click()
    time.sleep(.5) 

    # Copy result
    x,y  = pyautogui.locateCenterOnScreen('resource/FLIGHT_Max_Alt.PNG', confidence=0.5)
    pyautogui.click(x, y+25)
    pyautogui.hotkey('ctrl', 'c')
    result = float(pyperclip.paste().replace(",", ""))
    print('Result: ', result)

    # Close window
    x,y  = pyautogui.locateCenterOnScreen('resource/FLIGHT_X.PNG', confidence=0.5)
    pyautogui.click(x+25, y-25)
    time.sleep(0.2) 
    x,y  = pyautogui.locateCenterOnScreen('resource/FLIGHT_CLOSE_CONFIRM.PNG', confidence=0.5)
    pyautogui.click(x+50,y+45)

    return result



def parse_cdx1(filename):

    tree = ET.parse(filename)
    root = tree.getroot()

    print('Reading in... \n')
    tree.write(sys.stdout, encoding='unicode', xml_declaration=True)

    return tree, root


def cdx1_sub(infile, outfile, property, value):

    tree, root = parse_cdx1(infile)

    property = root.find(property)
    property.text = value
    
    tree.write(outfile, encoding='unicode', xml_declaration=False)








if __name__ == '__main__':

    # parse_cdx1('EXAMPLE_Loki.CDX1')
    # cdx1_sub('EXAMPLE_Loki.CDX1', 'MODIFIED.CDX1', ".//Fin/Span", '15')
    # open_and_run_RAS(r'C:\Users\emcke\Documents\GitHub_Repos\rasaero_optimizer\MODIFIED.CDX1')

    base_file = 'resource/EXAMPLE_Loki.CDX1'

    # var = './/Fin/Thickness'
    # values = [0.1, 0.125, 0.15, 0.175, 0.2, 0.225, 0.25]
    # values = [0.1, 0.15, 0.2, 0.25]
    # var = './/Fin/FX1'
    # values = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0]
    var = './/Fin/Span'
    values = [2.5, 3.0, 3.5, 4.0]

    results = [];
    temp_file = r'C:\Users\emcke\Documents\GitHub_Repos\rasaero_optimizer\MODIFIED_2.CDX1'

    print('Waiting...\n')
    time.sleep(1) 

    for val in values:
        cdx1_sub(base_file, temp_file, var, str(val))
        results.append(open_and_run_RAS(temp_file))

    plt.plot(values, results, marker='o')
    plt.xlabel(var)
    # plt.xlabel('TRAILING_EDGE Chamfer')
    plt.ylabel('Max Alt, ft')
    plt.title(base_file)
    plt.grid()
    plt.show()










 







    



