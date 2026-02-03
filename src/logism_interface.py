from dataclasses import field, dataclass
from typing import Any, Self
import xml.etree.ElementTree as ElementTree

Element = ElementTree.Element

def init_private_const(self : object, valname : str, value : Any):
  object.__setattr__(self,valname,value)
  object.__setattr__(self,f"_{type(self).__name__}{valname}",value)

@dataclass
class Project:
  fname : str
  logisim_command: str
  circuits : list[Project.Circuit] = field(init=False,default_factory=lambda: [])
  main_circuit : Project.Circuit = field(init=False)

  def __post_init__(self):
    self.tree = ElementTree.parse(self.fname)
    circuits = self.tree.findall('circuit')
    assert len(circuits) > 0, "No circuits found"
    for circuit_data in circuits:
      circuit = Project.Circuit(circuit_data)
      self.circuits.append(circuit)
      if circuit_data.get('name') == 'main':
        self.main_circuit = circuit
        break
    assert self.main_circuit is not None, "No main circuit found"

  def build(self):
    self.tree.write("tmp.circ")

  def run(self,*input_set : bool) -> list[bool]:
    for (val_to_set,intnl_input) in zip(input_set,self.main_circuit.inputs):
      intnl_input.set_value(val_to_set)

    self.build()
    #TEMP
    return []

  @dataclass
  class Circuit:
    root : Element
    inputs : list[Input] = field(init=False,default_factory=lambda: [])
    outputs : list[Output] = field(init=False,default_factory=lambda: [])

    def __post_init__(self):
      for component in self.root.findall('comp'):
        if component.get('name') == 'Pin':
          for attribute in component:
            component_type = attribute.get('name') 
            if component_type == 'tristate':
              self.inputs.append(Project.Circuit.Input(root=component))
            elif component_type == 'output': 
              self.outputs.append(Project.Circuit.Output(root=component))
      self.inputs.sort()
      self.outputs.sort()

    @dataclass(kw_only=True,frozen=True)
    class Component:
      root : Element
      label : str|None = field(init=False,default=None)

      def __post_init__(self) -> None:
        for attr in self.root:
          if attr.get('name') == 'label':
            object.__setattr__(self,'label', attr.get('val'))
            return

      def __lt__(self,other : Self) -> bool:
        match (self.label,other.label):
          case (None,None): return False
          case (str(a),None): return False
          case (None,str(b)): return True
          case (str(a),str(b)): return a.upper() < b.upper()
      
      def __gt__(self,other : Self): return not self.__lt__(other)

    @dataclass(kw_only=True,frozen=True)
    class Input(Component):
      __tristate : Element = field(init=False)
      
      def __post_init__(self) -> None:
        super().__post_init__()
        for attr in self.root:
          if attr.get('name') == 'tristate':
            init_private_const(self,'__tristate', attr)
            return
        assert False, "Failed to initialize Input"

      def get_value(self) -> bool:
        return self.__tristate.get('val') == 'true'
      
      def set_value(self, value : bool) -> None:
        self.__tristate.set('val','true' if value else 'false')

    @dataclass(kw_only=True,frozen=True)
    class Output(Component):
      __value : bool = field(init=False)

      def __post_init__(self) -> None:
        super().__post_init__()
        for attr in self.root:
          if attr.get('name') == 'output':
            init_private_const(self,'__value',attr.get('val'))
            return
        assert False, "Failed to initialize Output"
      
      def get_value(self) -> bool:
        return self.__value
