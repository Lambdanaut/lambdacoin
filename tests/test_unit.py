import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest

from lambdacoin.core import Block, Transaction, Client, LocalBroadcastNode
from lambdacoin.constants import SOLUTION_REWARD


class UnitTests(unittest.TestCase):

    def test_value_for_address(self):
        pass


if __name__ == '__main__':
    unittest.main()