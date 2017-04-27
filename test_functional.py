import unittest

from lambdacoin import Block, Transaction, Client, LocalBroadcastNode


class FunctionalTest(unittest.TestCase):
    def test_block_mining(self):
        pass

    def test_transactions(self):
        """Tests that transactions and rewards are distributed correctly

        Transaction value = 20
        Reward value = 1
        Transaction + reward = 21
        """

        transaction_value = 20

        blockchain1 = Block()
        blockchain2 = Block()

        client1 = Client(name='client1', blockchain=blockchain1)
        broadcast_node_1 = LocalBroadcastNode(client1)
        client2 = Client(name='client2', blockchain=blockchain2,
                         broadcast_nodes=[broadcast_node_1])
        broadcast_node_2 = LocalBroadcastNode(client2)
        client1.broadcast_nodes.append(broadcast_node_2)

        transaction = Transaction(
            outputs={client2.addresses[0]: transaction_value})

        client1.broadcast_transaction(transaction)

        solution = client2.mine_current_block()

        # Assessment of own value
        self.assertEqual(0, client1.total_value())
        self.assertEqual(21, client2.total_value())

        # Assessment of each other's value
        self.assertEqual(21, client1.total_value(client2.addresses))
        self.assertEqual(0, client2.total_value(client1.addresses))