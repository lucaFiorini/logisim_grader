import subprocess
from dataclasses import field, dataclass
from typing import Self
import xml.etree.ElementTree as ElementTree

@dataclass
class LogisimProject:

    class NotAnInputException(Exception):
        pass
    
    @dataclass
    class Circuit:
        @dataclass(kw_only=True,frozen=True)
        class Component:
            root : ElementTree.Element[str]
            label : str = field(init=False)

            def __post_init__(self) -> None:
                for attr in self.root:
                    if attr.get('label'):
                        object.__setattr__(self,'label', attr.get('val'))
                        return
                        

        @dataclass(kw_only=True,frozen=True)
        class Input(Component):
            __tristate : ElementTree.Element[str] = field(init=False)
            
            def __post_init__(self) -> None:
                ok = False
                for attr in self.root:
                    if attr.get('tristate') is not None:
                        ok = True
                        object.__setattr__(self,'__tristate', attr)
                        break
                
                assert ok, 'Failed to initialize Input'

            def get_value(self) -> bool:
                return self.__tristate.get('val') == 'true'
            
            def set_value(self, value : bool) -> None:
                self.__tristate.set('val','true' if value else 'false')

        @dataclass(kw_only=True,frozen=True)
        class Output(Component):
            __value : bool = field(init=False)

            def __post_init__(self) -> None:
                ok = False
                for attr in self.root:
                    if attr.get('output') is not None:
                        ok = True
                        object.__setattr__(self,'__value',attr.get('val'))
                        break
                
                assert ok, 'Failed to initialize Output'
            
            def get_value(self) -> bool:
                return self.__value
            
    def __init__(self,fname : str):
        self.tree = ElementTree.parse(fname)
        self.main : LogisimProject.Circuit 
        self.outputs : list[LogisimProject.Circuit.Component]
        self.inputs : list[LogisimProject.Circuit.Component]
        
        circuits = self.tree.findall('circuit')
        assert len(circuits) > 0, 'No circuits found'
        
        main_circuit = None
        for circuit in circuits:
            circuit_name = circuit.get('name')
            if circuit_name is not None and circuit_name == 'main':
                main_circuit = circuit
                break
        
        assert main_circuit is not None, 'No main circuit found'
        
        components = main_circuit.findall('componenet')
        
        for component in components:
            if component.get('name') is not None and component.get('name') == 'Pin':
                for attribute in component:
                    component_type = attribute.get('name') 
                    if component_type == 'tristate':
                        self.inputs.append(LogisimProject.Circuit.Input(root=component))
                    elif component_type == 'output': 
                        self.inputs.append(LogisimProject.Circuit.Output(root=component))
