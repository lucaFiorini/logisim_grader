import subprocess
import os
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable
from inspect import signature
from circuit_generator import get_tester_circuit_resource,get_num_inputs_outputs,create_connected_tester_circuit,CIRC_TO_REPLACE

PREFS_DIR = "/tmp/java-prefs"
os.makedirs(PREFS_DIR, exist_ok=True)

### Silencing Java errors
with open("logging.properties", "w") as f:
    f.write("java.util.prefs.level = WARNING\n")
JAVA_FLAGS = [
    f"-Djava.util.prefs.userRoot={PREFS_DIR}",
    f"-Djava.util.prefs.systemRoot={PREFS_DIR}",
    "-Djava.util.logging.config.file=logging.properties",
    "-Djava.awt.headless=true"
]

ATTACHMENTS = """{{ATTACHMENTS | e('py')}}"""
LOGISIM_COMMAND = ['java']+JAVA_FLAGS+['-jar','/usr/bin/logisim'] 

if len(ATTACHMENTS) == 0:
  raise Exception('Questa domanda accetta solo un file logisim (.circ) da caricare come allegato')

ATTACHMENTS = ATTACHMENTS.split(',')

if len(ATTACHMENTS) != 1:
  raise Exception('Questa domanda accetta solo un file logisim (.circ), per favore elimina gli altri')
submission = ATTACHMENTS[0]

parsed_submission = ET.parse(submission)
(CIRC_NUM_INPUTS,CIRC_NUM_OUTPUTS) = get_num_inputs_outputs(parsed_submission)
tester_data = create_connected_tester_circuit(parsed_submission)
CONNECTED_TESTER_NAME = '__TESTER_FILE.circ'

tester_data.write(CONNECTED_TESTER_NAME)

logisim_output = subprocess.check_output(
    LOGISIM_COMMAND+[
      CONNECTED_TESTER_NAME,
      '-tty','table',
      '-sub',CIRC_TO_REPLACE,submission
    ]
  ).decode('utf-8')

# Now that we have the output, let's actually check if it's right

@dataclass
class TestResult:
  @dataclass
  class Success:
    ...
  
  @dataclass
  class StructureFail:
    reason:str

  @dataclass
  class EvaluationFail:
    reason:str
  
  type Fail = StructureFail|EvaluationFail

  type Res = Success|Fail

  message : str
  result : Res
  pass

@dataclass
class Test[TestCallable: Callable[...,bool]]:
  exec : TestCallable

  def get_num_inputs(self):
    return len(signature(self.exec).parameters)
  
  def run(self,res : str,output_index : int) -> TestResult.Res:
    if self.get_num_inputs() > CIRC_NUM_INPUTS:
      return TestResult.StructureFail("Il circuito non ha abbastanza input per eseguire questo test")
    
    for input_set in res.splitlines():
      values = input_set.split('\t')    
      inputs = [v == '1' for v in values[0:CIRC_NUM_INPUTS]]
      if len(values) < CIRC_NUM_INPUTS+output_index:
        return TestResult.StructureFail("Output per questo test non trovato")
       
      output = values[CIRC_NUM_INPUTS+output_index]
      match output:
        case'x': return TestResult.EvaluationFail("Output non definito ('x')")
        case'E': return TestResult.EvaluationFail("Trovato un errore nell'output")
        case'1'|'0':
          expected = '1' if self.exec(*inputs[0:self.get_num_inputs()]) else '0'
          if output != expected:
            return TestResult.EvaluationFail("I valori non coincidono")
        case _: assert False,'never'
        
    return TestResult.Success()

res = {}
res["fraction"] = 0
res["got"] = ""

test_funcs : list[Callable[...,bool]] = {{TEST.testcode}}
tests : list[Test] = []
for test in test_funcs:
  tests.append(Test(test))

for test_index,test in enumerate(tests):
  res["got"]+="----------------------------\n"
  res["got"]+=f"Test #{test_index+1}"
  
  num_tests = len(tests)
  result = test.run(logisim_output,test_index)
  
  match result:
    case TestResult.Success() : res["fraction"] += 1 / num_tests
    case TestResult.StructureFail(reason) :
      res["got"] += f"Test Fallito: {reason}\n"
      
    case TestResult.EvaluationFail(reason) :
      res["got"] += f"Test Fallito: {reason}\n"
      for line_num in range(test.get_num_inputs()):
        res['got']+=chr(ord('A')+line_num)
      
      res["got"] += 'Out\n'

      for line_num,line in enumerate(logisim_output.splitlines()):
        if line_num >= 2**test.get_num_inputs(): #Trim output to prevent redundancy
          break
        vals = line.split('\t')
        for i,val in enumerate(vals):
          if i < test.get_num_inputs():
            res["got"] += val+'\t'
        
        res["got"] += vals[CIRC_NUM_INPUTS+test_index] #Print just the output
        res["got"] += '\n'

      

print(json.JSONEncoder().encode(res))