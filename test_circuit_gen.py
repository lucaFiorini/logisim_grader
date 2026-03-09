from circuit_generator import connect_test_circuit
import xml.etree.ElementTree as ET

with open('./circuits/tester.circ','r') as base_circ_file:
   base_circ = ET.ElementTree(file=base_circ_file)

with open('./circuits/tested.circ','r') as tested_circ_file:
   tested_circ = ET.ElementTree(file=tested_circ_file)
    
connect_test_circuit(base_circ,tested_circ)

base_circ.write('result.circ')