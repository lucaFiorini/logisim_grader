import subprocess
from dataclasses import dataclass
import xml.etree.ElementTree as ElementTree

class LANGS:
    ENG="eng"
    ITA="ita"

lang = LANGS.ITA

@dataclass
class LogisimProject:
    @dataclass
    class Circuit:
        @dataclass
        class Component:
            def __init__(self,root: ElementTree.Element):
                self.root = root
        @dataclass
        class Input(Component):
            pass
        @dataclass
        class Output(Component):
            pass
            
    def __init__(self,fname : str):
        self.tree = ElementTree.parse(fname)
        self.main : LogisimProject.Circuit 
        self.outputs : list[LogisimProject.Circuit.Component]
        self.inputs : list[LogisimProject.Circuit.Component]
        
        circuits = self.tree.findall("circuit")
        assert len(circuits) > 0, "No circuits found"
        
        main_circuit = None
        for circuit in circuits:
            circuit_name = circuit.get("name")
            if circuit_name is not None and circuit_name == "main":
                main_circuit = circuit
                break
        
        assert main_circuit is not None, "No main circuit found"
        
        components = main_circuit.findall("componenet")
        
        for component in components:
            if component.get("name") is not None and  component.get("name") == "Pin":
                for children in component:
                    pass #TODO