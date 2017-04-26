import unittest

from sillycoin import Client, Block


class SillyTest(unittest.TestCase):
    def test_block_mining(self):

        client = Client()

        print 'Generated Client with key: "{}"'.format(client.key.exportKey)

        block = Block(0, [], 1)

        print 'Generated block: "{}"'.format(block.block_hash)

        print 'Mining the block...'
        solution = client.mine(block)

        print 'Block mined! Puzzle solution: "{}"'.format(solution)
