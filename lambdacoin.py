import json
import logging
import sys

from Crypto.Random import random
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA

import constants
from utils import rando


logging.basicConfig(stream=sys.stdout, level='DEBUG')
logger = logging.getLogger('lambdacoin')


class Block(object):
    def __init__(self, hash=None, transactions=None, target=1, prev_block=None,
            next_block=None):
        self.hash = hash or SHA.new(str(rando())).hexdigest()
        self.transactions = transactions or []
        self.target = target

        self.prev_block = prev_block
        self.next_block = next_block

        # Puzzle is a combination of all of the transaction's hashes together
        self.puzzle = self._updated_puzzle()

    def add_transaction(self, transaction):
        if not self.has_transaction(transaction):
            self.transactions.append(transaction)
            self.puzzle = self._updated_puzzle()

    def has_transaction(self, transaction):
        return transaction.hash in [t.hash for t in self.transactions]

    def verify(self, nonce):
        """
        Generates a hash based on the transaction text, given an nonce, and
        checks whether the first `target` characters of the generated hash 
        are "0"s

        The higher the target value, the more 0s required, and the more
        unlikely it is to verify. 

        :param nonce: str
        :return Bool:
        """
        text = self.puzzle + nonce
        h = SHA.new(text).hexdigest()
        return h[:self.target] == '0' * self.target

    def _updated_puzzle(self):
        return ''.join([t.hash for t in self.transactions])


class Transaction(object):
    def __init__(self, recipients, value, hash=None, version=None):
        self.recipients = recipients
        self.value = value
        self.hash = hash or SHA.new(str(rando())).hexdigest()
        self.version = version or constants.version

    def sign(self, key):
        """Adds signature to the Transaction"""

        self.key = key  # Public key of sender
        self.sig = self.key.sign(self.hash, rando())  # Signature of sender

    def to_dict(self):
        doc = {
            'version': self.version, # lambdacoin protocol version
            'hash': self.hash,
            'size': 123,

            'in': [
                {
                    'hash': 'abc',
                    'n': 0
                },
            ],

            'out': {
                'value': 0.1,
                'hash': 'qwrt'
            },

        }

        return doc


def transaction_from_dict(doc):
    recipients = doc.get('out')
    version = doc.get('version')
    hash = doc.get('hash')

    return Transaction(recipients, 0.01, hash, version)


class BroadcastNode(object):
    """Abstract class to implement remote nodes to broadcast data to"""
    def broadcast(self, data):
        raise NotImplementedError()


class LocalBroadcastNode(BroadcastNode):
    """
    Broadcast node for testing broadcasting between clients within a single
    Python application
    """
    def __init__(self, client):
        self.client = client

    def broadcast(self, data):
        self.client.receive_broadcast(data)


class Client(object):
    def __init__(self, blockchain=None, broadcast_nodes=None):
        self.key = RSA.generate(1024)
        self.addresses = [self.generate_address()]
        self.blockchain = blockchain

        self.broadcast_nodes = broadcast_nodes or []

        # Current block being worked on
        # Includes transactions waiting to be confirmed
        self.current_block = Block()

    def generate_address(self):
        return SHA.new(str(rando())).hexdigest()

    def mine(self, block, start=0, end=2000):
        for x in range(start, end):
            if block.verify(str(x)):
                return str(x)

    def mine_current_block(self, start=0, end=2000):
        return self.mine(self.current_block)

    def broadcast_transaction(self, transaction):
        transaction.sign(self.key)

        doc = transaction.to_dict()
        doc = self.package_for_broadcast('transaction', doc)
        data = json.dumps(doc)

        return self.broadcast(data)

    def broadcast_block_solution(self):
        pass

    def broadcast(self, data):
        results = [node.broadcast(data) for node in self.broadcast_nodes]
        return results

    def package_for_broadcast(self, type, data):
        """Given dict, wraps in broadcast dict"""
        packaged = {
            'type': type,
            'package': data,
        }

        return packaged

    def receive_broadcast(self, data):
        """Callback for when a broadcast is received from another node"""

        # Parse broadcast
        doc = json.loads(data)

        b_type = doc.get('type')
        if b_type == 'transaction':
            transaction_doc = doc.get('package')
            transaction = transaction_from_dict(transaction_doc)

            # Propogate and save the transaction if it's new
            if not self.current_block.has_transaction(transaction):
                logger.debug('Broadcasting transaction {}'.format(
                    transaction.hash))
                self.current_block.add_transaction(transaction)
                self.broadcast(data)

        else:
            return

if __name__ == '__main__':
    client1 = Client()
    broadcast_node_1 = LocalBroadcastNode(client1)
    client2 = Client(broadcast_nodes=[broadcast_node_1])
    broadcast_node_2 = LocalBroadcastNode(client2)
    client1.broadcast_nodes.append(broadcast_node_2)

    print 'Generated client with key: "{}"'.format(client1.key.exportKey())

    transaction = Transaction([client2.addresses[0]], 0.1)
    print 'Created transaction {}'.format(transaction.hash)

    print 'Broadcasting a transaction...'
    client1.broadcast_transaction(transaction)

    print 'Mining the block...'
    solution = client2.mine_current_block()

    print 'Block mined! Puzzle solution: "{}"'.format(solution)
