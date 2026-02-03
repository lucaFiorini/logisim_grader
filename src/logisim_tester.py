import itertools
from logism_interface import Project
from typing import Callable, ClassVar, Type, Union, assert_never
from inspect import signature
from dataclasses import dataclass

@dataclass(frozen=True)
class Err:
  msg : str

@dataclass(frozen=True)
class Ok:
  val : bool

type Result = Ok|Err  

@dataclass(frozen=True)
class TestResult:
  success : bool 
  msg : str

@dataclass(frozen=True)
class TestSet:
  project : Project
  tests : list[TestSet.Test]

  @dataclass(frozen=True)
  class Test:
    value: int
    test : Callable[...,bool]

    def run(self,*args : bool) -> Result:
      test_input_count = len(signature(self.test).parameters)
      if len(args) < test_input_count:
        return Err("Not enough arguments found to run this test")
      return Ok(self.test(*args[0:test_input_count]))

  def execute(self) -> tuple[int,list[TestResult]]:
    """Executes a TestSet"""

    def test_all_permutations(test : TestSet.Test, input_len : int) -> TestResult:
      """Tests all permutations of a given test, will return on first failure or wrong result."""
      input_permutations = itertools.product([False,True] * input_len,repeat=input_len)
      for input_set in input_permutations:
        results = [res.run(*input_set) for res in self.tests]
        for res in results:
          match res:
            case Err(err): 
              return TestResult(False,err)
            case Ok(x): 
                y = self.project.run(*input_set)
                if x != y: return TestResult(False,f"Test faield, expected {x} got {y}")
            case _: assert_never(x)
      return TestResult(True,"Test passed successfully")
    
    result_set : list[TestResult] = []
    points_total = 0
    for test in self.tests:
      result = test_all_permutations(test, len(self.project.main_circuit.inputs))
      if result.success: points_total += test.value
      result_set.append(result)

    return (points_total,result_set)
  