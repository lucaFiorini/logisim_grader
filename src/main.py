from logism_interface import *
from logisim_tester import *

def main():
  project = Project(
    'C:\\Users\\Fiorini\\Documents\\GitHub\\logisim-grader\\logisim_test.circ',
    '.\\logisim-win-2.7.1.exe'
  )
  project.run(False,True,False)
main()