import dataclasses

from typing import Generator,Protocol
from dataclasses import dataclass
from enum import Enum, auto

@dataclass
class Coord:
  """
  Standard Coordiante system, \n
  `x` Is horizontal offset (left to right) \n
  `y` Is vertical offset (top to bottom) \n
  """
  x : int
  y : int
  
  def __iter__(self) -> Generator[int] :
    return (getattr(self, field.name) for field in dataclasses.astuple(self))


class Direction(Enum):
  UP = auto()
  DOWN = auto()
  LEFT = auto()
  RIGHT = auto()

@dataclass(kw_only=True)
class Wire:
  origin : Coord
  length : int
  direction : Direction
  
  def get_end(self) -> Coord:
    match self.direction:
      case Direction.UP: return Coord(self.origin.x, self.origin.y - self.length)
      case Direction.DOWN: return Coord(self.origin.x, self.origin.y + self.length)
      case Direction.LEFT: return Coord(self.origin.x - self.length, self.origin.y)
      case Direction.RIGHT: return Coord(self.origin.x + self.length, self.origin.y)

@dataclass
class Input:
  origin : Coord

@dataclass
class Output:
  origin : Coord