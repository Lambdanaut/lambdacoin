import os
import json
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest

from lambdacoin.core import Block, Transaction, Client, LocalBroadcastNode
from lambdacoin.constants import SOLUTION_REWARD
from lambdacoin.exceptions import UnknownBroadcastType


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        self.blockchain1 = Block()
        self.blockchain2 = Block()

        self.client1 = Client(name='client1', blockchain=self.blockchain1)
        self.broadcast_node_1 = LocalBroadcastNode(self.client1)
        self.client2 = Client(name='client2', blockchain=self.blockchain2,
                         broadcast_nodes=[self.broadcast_node_1])
        self.broadcast_node_2 = LocalBroadcastNode(self.client2)
        self.client1.register_broadcast_node(self.broadcast_node_2)

    def test_transactions(self):
        """Tests that transactions and rewards are distributed correctly

        Transaction value = 20
        Reward value = 1
        Transaction + reward = 21
        """

        transaction_value = 20.5

        transaction = Transaction(
            outputs={self.client2.addresses[0]: transaction_value})

        self.client1.broadcast_transaction(transaction)

        self.client2.mine_current_block()

        expected_final_value = transaction_value + SOLUTION_REWARD

        # Assessment of own value
        self.assertEqual(0, self.client1.total_value())
        self.assertEqual(expected_final_value, self.client2.total_value())

        # Assessment of each other's value
        self.assertEqual(
            expected_final_value, self.client1.total_value(self.client2.addresses))
        self.assertEqual(0, self.client2.total_value(self.client1.addresses))

    def test_unknown_broadcast_type(self):
        """Tests that an UnknownBroadcastType exception is raised if an
        unknown broadcast type is received"""

        doc = self.client1.current_block.to_dict()
        doc = self.client1.package_for_broadcast(
            'DUMMY-FAKE-BROADCAST-TYPE', doc)
        data = json.dumps(doc)

        with self.assertRaises(UnknownBroadcastType):
            self.client1.broadcast(data)

if __name__ == '__main__':
    unittest.main()