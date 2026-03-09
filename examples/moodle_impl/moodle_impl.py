import subprocess
import os
import json
from dataclasses import dataclass
from typing import Callable
from inspect import signature

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

#Perhaps I should upload this via FTP and have a static path here instead
RAW_LOGISIM_MASTER_CIRCUIT = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><project source="2.7.1" version="1.0">This file is intended to be loaded by Logisim (http://www.cburch.com/logisim/).<lib desc="#Wiring" name="0"/><lib desc="#Gates" name="1"/><lib desc="#Plexers" name="2"/><lib desc="#Arithmetic" name="3"/><lib desc="#Memory" name="4"><tool name="ROM"><a name="contents">addr/data: 8 800</a></tool></lib><lib desc="#I/O" name="5"/><lib desc="#Base" name="6"><tool name="Text Tool"><a name="text" val=""/><a name="font" val="SansSerif plain 12"/><a name="halign" val="center"/><a name="valign" val="base"/></tool></lib><lib desc="file#dummy.circ" name="7"/><main name="main"/><options><a name="gateUndefined" val="ignore"/><a name="simlimit" val="1000"/><a name="simrand" val="0"/></options><mappings><tool lib="6" map="Button2" name="Menu Tool"/><tool lib="6" map="Button3" name="Menu Tool"/><tool lib="6" map="Ctrl Button1" name="Menu Tool"/></mappings><toolbar><tool lib="6" name="Poke Tool"/><tool lib="6" name="Edit Tool"/><tool lib="6" name="Text Tool"><a name="text" val=""/><a name="font" val="SansSerif plain 12"/><a name="halign" val="center"/><a name="valign" val="base"/></tool><sep/><tool lib="0" name="Pin"><a name="tristate" val="false"/></tool><tool lib="0" name="Pin"><a name="facing" val="west"/><a name="output" val="true"/><a name="labelloc" val="east"/></tool><tool lib="1" name="NOT Gate"/><tool lib="1" name="AND Gate"/><tool lib="1" name="OR Gate"/></toolbar><circuit name="main"><a name="circuit" val="main"/><a name="clabel" val=""/><a name="clabelup" val="east"/><a name="clabelfont" val="SansSerif plain 12"/><wire from="(230,30)" to="(230,160)"/><wire from="(240,50)" to="(360,50)"/><wire from="(220,150)" to="(270,150)"/><wire from="(310,150)" to="(310,160)"/><wire from="(220,10)" to="(220,150)"/><wire from="(250,70)" to="(360,70)"/><wire from="(210,180)" to="(250,180)"/><wire from="(230,160)" to="(270,160)"/><wire from="(170,210)" to="(170,240)"/><wire from="(210,170)" to="(240,170)"/><wire from="(240,170)" to="(270,170)"/><wire from="(310,160)" to="(330,160)"/><wire from="(250,70)" to="(250,180)"/><wire from="(150,240)" to="(170,240)"/><wire from="(190,200)" to="(210,200)"/><wire from="(210,160)" to="(230,160)"/><wire from="(250,180)" to="(270,180)"/><wire from="(300,160)" to="(310,160)"/><wire from="(300,150)" to="(310,150)"/><wire from="(210,150)" to="(220,150)"/><wire from="(220,10)" to="(360,10)"/><wire from="(240,50)" to="(240,170)"/><wire from="(230,30)" to="(360,30)"/><comp lib="0" loc="(330,160)" name="Pin"><a name="facing" val="west"/><a name="output" val="true"/><a name="labelloc" val="east"/></comp><comp lib="0" loc="(360,70)" name="Pin"><a name="facing" val="west"/><a name="output" val="true"/><a name="labelloc" val="east"/></comp><comp lib="0" loc="(360,30)" name="Pin"><a name="facing" val="west"/><a name="output" val="true"/><a name="labelloc" val="east"/></comp><comp lib="0" loc="(190,190)" name="Splitter"><a name="fanout" val="4"/><a name="incoming" val="4"/></comp><comp lib="4" loc="(190,190)" name="Counter"><a name="width" val="4"/><a name="max" val="0xf"/></comp><comp lib="7" loc="(300,160)" name="main"/><comp lib="0" loc="(360,10)" name="Pin"><a name="facing" val="west"/><a name="output" val="true"/><a name="labelloc" val="east"/></comp><comp lib="0" loc="(360,50)" name="Pin"><a name="facing" val="west"/><a name="output" val="true"/><a name="labelloc" val="east"/></comp><comp lib="0" loc="(210,200)" name="Pin"><a name="facing" val="west"/><a name="output" val="true"/><a name="label" val="halt"/><a name="labelloc" val="east"/></comp><comp lib="0" loc="(150,240)" name="Clock"/></circuit></project>'
    
LOGISIM_COMMAND = ['java']+JAVA_FLAGS+['-jar','/usr/bin/logisim'] 
LOGISIM_MASTER_CIRCUIT = "master.circ"
LOGISIM_DUMMY_CIRCUIT = "dummy.circ"

if len(ATTACHMENTS) == 0:
  raise Exception('Questa domanda accetta solo un file logisim (.circ) da caricare come allegato')

ATTACHMENTS = ATTACHMENTS.split(',')

if len(ATTACHMENTS) != 1:
  raise Exception('Questa domanda accetta solo un file logisim (.circ), per favore elimina gli altri')

#TODO: Replace RAW_LOGISIM_MASTER_CIRCUIT with real shit
with open(LOGISIM_MASTER_CIRCUIT,"w") as f:
  print(RAW_LOGISIM_MASTER_CIRCUIT,file=f)

submission = ATTACHMENTS[0]
logisim_output = subprocess.check_output(
    LOGISIM_COMMAND+[
      LOGISIM_MASTER_CIRCUIT,
      '-tty','table',
      '-sub',LOGISIM_DUMMY_CIRCUIT,submission
    ]
    ).decode('utf-8')

# Now that we have the output, let's actually check if it's right

@dataclass
class TestResult:
  @dataclass
  class Success:
    ...
  @dataclass
  class Fail:
    reason:str
  
  type Res = Success|Fail

  message : str
  result : Res
  pass

@dataclass
class Test[TestCallable: Callable[...,bool]]:
  exec : TestCallable

  def get_num_args(self):
    return len(signature(self.exec).parameters)
  
  def run(self,res : str) -> TestResult.Res:
    for input_set in res.splitlines():
      values = input_set.split('\t')    
      inputs = [v == '1' for v in values[0:self.get_num_args()]]
      output = values[-1]
      match output:
        case'x': return TestResult.Fail("Output non definito ('x')")
        case'E': return TestResult.Fail("Trovato un errore nell'output")
        case'1'|'0':
          expected = '1' if self.exec(*inputs) else '0'
          if output != expected:
            return TestResult.Fail("I valori non coincidono")
        case _: assert False,'never'
        
    return TestResult.Success()

res = {}
test = Test({{TEST.testcode}})
result = test.run(logisim_output)
match result:
  case TestResult.Success() : res["fraction"] = 1
  case TestResult.Fail(reason) :
    res["fraction"] = 0
    res["got"] = reason+'\n'
    for line_num in range(test.get_num_args()):
      match line_num:
        case 0: res["got"] += 'A\t'
        case 1: res["got"] += 'B\t'
        case 2: res["got"] += 'C\t'
        case 3: res["got"] += 'D\t'
    
    res["got"] += 'Out\n'

    for line_num,line in enumerate(logisim_output.splitlines()):
      if line_num >= 2**test.get_num_args(): #Trim output to prevent redundancy
        break
      vals = line.split('\t')
      for line_num,val in enumerate(vals):
        if line_num < test.get_num_args():
          res["got"] += val+'\t'
        
      res["got"] += vals[-1] #Print just the output
      res["got"] += '\n'

    

print(json.JSONEncoder().encode(res))