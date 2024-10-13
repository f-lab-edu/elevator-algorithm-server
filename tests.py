import unittest

from main import Elevator

class Test_Elevator_Scenario(unittest.TestCase):
    def setUp(self) -> None:
        self.elevator = Elevator("ELEVATOR1")
