from logisim_types import Coord,Direction,Wire,Output
import xml.etree.ElementTree as ET
from importlib.resources import files,as_file

#The filename of the placeholder circuit to be replaced in the tester project
CIRC_TO_REPLACE = 'placeholder.circ'
  
def get_tester_circuit_resource():
  return as_file(files(__package__).joinpath("circuits/tester.circ"))

def get_tester_circuit_parsed():
  with get_tester_circuit_resource() as res:
    return ET.parse(res)

def get_num_inputs_outputs(circ : ET.ElementTree[ET.Element[str]]) -> tuple[int,int]:
  root = circ.getroot()
  assert root is not None
  
  evaluated_circ_elem = next(
    c for c in root.findall("circuit") if c.get("name") == "main"
  )
  
  pins = [c for c in evaluated_circ_elem.findall("comp") if c.get("name") == "Pin"]
  
  n_inputs = sum(
    1 for p in pins
    if not any(
      a.get("name") == "output" and a.get("val") == "true" for a in p
    )
  )
  n_outputs = sum(
    1 for p in pins
    if any(
      a.get("name") == "output" and a.get("val") == "true" for a in p
    )
  )
  return (n_inputs,n_outputs)
  
def create_connected_tester_circuit(evaluated_circuit : ET.ElementTree[ET.Element[str]]) -> ET.ElementTree[ET.Element[str]]:
  
  tester_circuit = get_tester_circuit_parsed()
  root = tester_circuit.getroot()
  assert root is not None
  
  #Get Number of Inputs
  (n_inputs,n_outputs) = get_num_inputs_outputs(evaluated_circuit)
  
  if n_inputs == 0 or n_outputs == 0:
    raise RuntimeError("Circuit does not have enough inputs or outputs")
  
  #Get other parts
  main_circ_elem = next(
    c for c in root.findall("circuit") if c.get("name") == "main"
  )
  splitter_elem = next(
    c for c in main_circ_elem.findall("comp")
    if c.get("name") == "Splitter"
  )
  counter_elem = next(
    c for c in main_circ_elem.findall("comp")
    if c.get("name") == "Counter"
  )
  placeholder_circuit = next(
    c for c in main_circ_elem.findall("comp")
    if c.get("lib") == "7" #This is completely arbitrary.
  )
  next(
    a for a in counter_elem
    if a.get('name') == 'width'
  ).set('val',str(n_inputs))  
  next(
    a for a in splitter_elem
    if a.get('name') == 'fanout'
  ).set('val',str(n_inputs))
  next(
    a for a in splitter_elem
    if a.get('name') == 'incoming'
  ).set('val',str(n_inputs))
  
  splitter_loc_str = splitter_elem.get("loc")  # e.g. "(70,1460)"
  assert splitter_loc_str is not None
  splitter_loc_str = splitter_loc_str.strip("()")
  sx, sy = (int(v) // 10 for v in splitter_loc_str.split(","))
  splitter_loc = Coord(sx, sy)
  
  lowest_splitter_output = Coord(splitter_loc.x+2, splitter_loc.y - 1)

  #Now that we have found where the lowest splitter output is, we calculate
  
  support_wires : list[Wire] = []
  display_wires : list[Wire] = []
  insertion_wires : list[Wire] = []
  
  for i in range(n_inputs):
    horizontal_wire_1 = Wire(
        origin=Coord(lowest_splitter_output.x, lowest_splitter_output.y - i),
        length=1 + n_inputs - i,
        direction=Direction.RIGHT
      )
    vertical_wire_1 = Wire(
        origin=horizontal_wire_1.get_end(),
        length=n_inputs + n_outputs + 5,
        direction=Direction.UP
      )
    insertion_wire = Wire(
      origin=horizontal_wire_1.get_end(),
      length=i + 3,
      direction=Direction.RIGHT
    )
    display_wire = Wire(
      origin=vertical_wire_1.get_end(),
      length=i + 3,
      direction=Direction.RIGHT
    )
    support_wires.append(horizontal_wire_1)
    support_wires.append(vertical_wire_1)
    insertion_wires.append(insertion_wire)
    display_wires.append(display_wire)


  #Adjusting the coordinates of the dummy circuit to fir the incoming circuit requires a few arbitrary steps
  #Notes:
  #The origin is the top output's coordinate
  #The vertical alignment of pins is based upon a distribution of pins (in/out) around the origin, 
  #With a bias to placing new pins below the origin. 
  #All steps are in reference to the coordinates of the first input

  test_circ_origin = insertion_wires[-1].get_end() 
  test_circ_origin.x += 3
  test_circ_origin.y += (n_inputs-n_outputs) // 2
    
  outputs : list[Output] = []
  #It follows that all subsequent outputs will start from the origin of the test circ
  for i in range(n_outputs):
    outputs.append(Output(Coord(test_circ_origin.x,test_circ_origin.y+i)))
  
  #I will also add outputs at the end of all the display wires  
  for wire in display_wires:
    outputs.append(Output(wire.get_end()))
  
  #Now that I have organized all of the extra elements, I will start adding them to the circuit.
  
  main_circ_elem = next(
    c for c in root.findall("circuit") if c.get("name") == "main"
  )

  def coord_str(c: Coord) -> str:
    return f"({c.x*10},{c.y*10})"

  def add_wire(elem: ET.Element, start: Coord, end: Coord) -> None:
    wire_elem = ET.SubElement(elem, "wire")
    wire_elem.set("from", coord_str(start))
    wire_elem.set("to", coord_str(end))

  def add_output_pin(elem: ET.Element, loc: Coord) -> None:
    comp_elem = ET.SubElement(elem, "comp")
    comp_elem.set("lib", "0")
    comp_elem.set("loc", coord_str(loc))
    comp_elem.set("name", "Pin")
    facing = ET.SubElement(comp_elem, "a")
    facing.set("name", "facing")
    facing.set("val", "west")
    output = ET.SubElement(comp_elem, "a")
    output.set("name", "output")
    output.set("val", "true")
    labelloc = ET.SubElement(comp_elem, "a")
    labelloc.set("name", "labelloc")
    labelloc.set("val", "east")

  placeholder_circuit.set('loc',coord_str(test_circ_origin))

  for wire in support_wires:
    add_wire(main_circ_elem, wire.origin, wire.get_end())

  for wire in insertion_wires:
    add_wire(main_circ_elem, wire.origin, wire.get_end())

  for wire in display_wires:
    add_wire(main_circ_elem, wire.origin, wire.get_end())

  for output in outputs:
    add_output_pin(main_circ_elem, output.origin)
    
  return tester_circuit