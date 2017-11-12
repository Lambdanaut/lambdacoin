import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest

from lambdacoin.core import Block, Transaction, Client, LocalBroadcastNode
from lambdacoin.constants import SOLUTION_REWARD


class UnitTests(unittest.TestCase):

    def test_value_for_address(self):
        """Tests that transactions and rewards are distributed correctly

        Transaction value = 20
        Reward value = 1
        Transaction + reward = 21
        """

        blockchain = Block()

        client1 = Client(name='client1', blockchain=blockchain1)
        broadcast_node_1 = LocalBroadcastNode(client1)
        client2 = Client(name='client2', blockchain=blockchain2,
                         broadcast_nodes=[broadcast_node_1])
        broadcast_node_2 = LocalBroadcastNode(client2)
        client1.broadcast_nodes.append(broadcast_node_2)

        transaction = Transaction(
            outputs={client2.addresses[0]: transaction_value})

        client1.broadcast_transaction(transaction)

        client2.mine_current_block()

        expected_final_value = transaction_value + SOLUTION_REWARD

        # Assessment of own value
        self.assertEqual(0, client1.total_value())
        self.assertEqual(expected_final_value, client2.total_value())

        # Assessment of each other's value
        self.assertEqual(expected_final_value, client1.total_value(client2.addresses))
        self.assertEqual(0, client2.total_value(client1.addresses))

if __name__ == '__main__':
    unittest.main()