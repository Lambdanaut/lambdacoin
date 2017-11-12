"""

TODO:

* Add Transaction inputs
*
* Saving Blockchain to disk

"""

import json
import logging
import sys
from typing import List, Optional

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA

from lambdacoin.broadcast import LocalBroadcastNode
import lambdacoin.constants as constants
from lambdacoin.exceptions import UnknownBroadcastType
import lambdacoin.utils
from lambdacoin.utils import pretty_hash, rando

logging.basicConfig(stream=sys.stdout, level='DEBUG')
logger = logging.getLogger('lambdacoin')


class Block(object):
    def __init__(self, hash=None, transactions=None, gen_transaction=None,
                 target=None, prev_block=None, next_block=None, solution=None,
                 version=None):
        self.hash = hash or lambdacoin.utils.generate_hash()
        self.transactions = transactions or []
        self.gen_transaction = gen_transaction
        self.target = 1 if target is None else target
        self.solution = solution
        self.version = version or constants.VERSION

        self.prev_block = prev_block
        self.next_block = next_block

        # Puzzle is a combination of all of the transaction's hashes together
        self.puzzle = self._updated_puzzle()

    def add_next(self, next_block: 'Block'):
        self.next_block = next_block
        next_block.prev_block = self

    def add_transaction(self, transaction: 'Transaction'):
        if not self.has_transaction(transaction):
            self.transactions.append(transaction)
            self.puzzle = self._updated_puzzle()

    def has_transaction(self, transaction: 'Transaction') -> bool:
        return transaction.hash in [t.hash for t in self.transactions]

    def verify(self, nonce: str = None) -> bool:
        """
        Generates a hash based on the transaction text, given an nonce, and
        checks whether the first `target` characters of the generated hash 
        are "0"s

        The higher the target value, the more 0s required, and the more
        unlikely it is to verify. 
        """
        nonce = nonce or self.solution

        text = self.puzzle + nonce
        h = SHA.new(text.encode('utf-8')).hexdigest()
        return h[:self.target] == '0' * self.target

    def block_in_past(self, block_hash: str) -> bool:
        """
        Returns whether the given block hash is the hash of any previous blocks
        """
        current_block = self
        while current_block is not None:
            if block_hash == current_block.hash:
                return True
            current_block = current_block.prev_block

        return False

    def value_for_address(self, address: str):
        """Returns the value an address owns in this blockchain"""
        value = 0

        current_block = self
        # Loop through blockchain until we hit the Genesis block
        while current_block is not None:
            if current_block.gen_transaction is not None:
                value += current_block.gen_transaction.value_for_address(
                    address)

            for transaction in current_block.transactions:
                value += transaction.value_for_address(address)

            current_block = current_block.prev_block

        return value

    def _updated_puzzle(self):
        return ''.join([t.hash for t in self.transactions])

    def to_dict(self):
        gen_transaction = None
        if self.gen_transaction is not None:
            gen_transaction = self.gen_transaction.to_dict()

        doc = {
            'version': self.version,  # lambdacoin protocol version
            'hash': self.hash,
            'solution': self.solution,
            'gen_transaction': gen_transaction,
            'transactions': [t.hash for t in self.transactions],
        }

        return doc

    @staticmethod
    def from_dict(doc, given_transactions: List['Transaction']):
        """
        Attempts to convert a block doc into a Block object by matching
        the transaction hashes with a list of given transactions

        :param doc: dict to convert to Block
        :param given_transactions: Transactions waiting to be confirmed
        """
        given_transaction_hashes = {t.hash: t for t in given_transactions}

        version = doc.get('version')
        hash = doc.get('hash')
        solution = doc.get('solution')
        gen_transaction_doc = doc.get('gen_transaction')
        transaction_hashes = doc.get('transactions')

        gen_transaction = None
        if gen_transaction_doc is not None:
            gen_transaction = Transaction.from_dict(gen_transaction_doc)

        # Match transaction hashes
        transactions = []
        if transaction_hashes is not None:
            for t_hash in transaction_hashes:
                if t_hash in given_transaction_hashes:
                    t_match = given_transaction_hashes[t_hash]
                    transactions.append(t_match)

        return Block(version=version, hash=hash, solution=solution,
                     transactions=transactions,
                     gen_transaction=gen_transaction)


class Transaction(object):
    def __init__(self, inputs=None, outputs=None, hash=None, version=None):
        self.inputs = inputs or []
        self.outputs = outputs or {}  # {address: value}
        self.hash = hash or lambdacoin.utils.generate_hash()
        self.version = version or constants.VERSION

        self.key = None
        self.sig = None

    def sign(self, key):
        """Adds signature to this Transaction"""

        # Public key of sender
        self.key = key.publickey()

        # Signature of sender
        self.sig = key.sign(
            int(self.hash, 16),  # Convert hex hash string to int
            rando())

    def verify(self):
        if self.key is not None and self.sig is not None:
            return self.key.verify(self.hash, self.sig)
        else:
            return False

    def value_for_address(self, address: str):
        """Returns the value an address owns in this transaction"""
        value = 0

        for out_address, out_value in self.outputs.items():
            if address == out_address:
                value += out_value

        return value

    def to_dict(self):
        doc = {
            'version': self.version,  # lambdacoin protocol version
            'hash': self.hash,
            'size': 123,
            'inputs': [
                {
                    # Hash of input transaction
                    'hash': 'abc',
                    # n is 'vout' Index in list of outputs from input transaction
                    'n': 0,
                }
            ],
            'outputs': self.outputs,
        }

        return doc

    @staticmethod
    def from_dict(doc: dict) -> 'Transaction':
        inputs = doc.get('inputs')
        outputs = doc.get('outputs')
        version = doc.get('version')
        hash = doc.get('hash')

        return Transaction(
            inputs, outputs, hash, version)


class Client(object):
    def __init__(self, name=None, addresses=None, blockchain=None,
                 broadcast_nodes=None):
        self.name = name
        self.key = RSA.generate(1024)
        self.addresses = addresses or [self.generate_address()]
        self.blockchain = blockchain

        self.broadcast_nodes = broadcast_nodes or []

        # Current block being worked on
        # Includes transactions waiting to be confirmed
        self.current_block = Block()

    def generate_address(self) -> str:
        return lambdacoin.utils.generate_hash()

    def total_value(self, addresses: List[str] = None) -> float:
        """
        Returns the total value from all transactions owned by the given
        addresses
        """
        if addresses is None:
            addresses = self.addresses
        return sum([self.blockchain.value_for_address(addr)
                    for addr in addresses])

    def mine(self, block: 'Block', start=0, end=2000) -> Optional[str]:
        for x in range(start, end):
            if block.verify(str(x)):
                return str(x)

    def mine_current_block(self, start=0, end=2000):
        solution = self.mine(self.current_block, start, end)

        if solution is not None:
            logger.debug('Client {} found solution of {} for block {}'.format(
                self.name, solution, pretty_hash(self.current_block.hash)))

            # Create and broadcast the gen transaction
            gen_transaction = Transaction(
                outputs={self.addresses[0]: constants.SOLUTION_REWARD}
            )

            # Broadcast the block with the solution
            self.current_block.solution = solution
            self.current_block.gen_transaction = gen_transaction
            self.blockchain.add_next(self.current_block)
            self.blockchain = self.current_block
            self.broadcast_solution()

        return solution

    def register_broadcast_node(self, broadcast_node):
        self.broadcast_nodes.append(broadcast_node)

    def broadcast_transaction(self, transaction: 'Transaction') -> list:
        """Signs a transaction and sends it to the network"""
        transaction.sign(self.key)

        doc = transaction.to_dict()
        doc = self.package_for_broadcast(constants.B_TYPE_TRANSACTION, doc)
        data = json.dumps(doc)

        return self.broadcast(data)

    def broadcast_solution(self) -> list:
        doc = self.current_block.to_dict()
        doc = self.package_for_broadcast(constants.B_TYPE_SOLUTION, doc)
        data = json.dumps(doc)

        return self.broadcast(data)

    def broadcast(self, data: str):
        results = [node.broadcast(data) for node in self.broadcast_nodes]
        return results

    def package_for_broadcast(self, broadcast_type: str, data: dict) -> dict:
        """Given dict, wraps in broadcast dict"""
        packaged = {
            'type': broadcast_type,
            'package': data,
        }

        return packaged

    def receive_broadcast(self, data: str):
        """Callback for when a broadcast is received from another node"""

        # Parse broadcast
        doc = json.loads(data)

        b_type = doc.get('type')
        if b_type == 'transaction':
            transaction_doc = doc.get('package')
            transaction = Transaction.from_dict(transaction_doc)

            logger.debug('Client {} received transaction {}'.format(
                self.name, pretty_hash(transaction.hash)))

            # Propagate and save the transaction if it's new
            if not self.current_block.has_transaction(transaction):
                logger.debug('Client {} broadcasting transaction {}'.format(
                    self.name, pretty_hash(transaction.hash)))
                self.current_block.add_transaction(transaction)
                self.broadcast(data)

        elif b_type == 'solution':
            solution_doc = doc.get('package')
            solution = Block.from_dict(
                solution_doc, self.current_block.transactions)

            logger.debug('Client {} received solution for block {}'.format(
                self.name, pretty_hash(solution.hash)))

            # Check if solution is correct
            if not self.blockchain.block_in_past(solution.hash):
                verified = solution.verify()
                if verified:
                    logger.debug(
                        'Client {} verified solution {} for block {}'.format(
                            self.name, solution.solution,
                            pretty_hash(solution.hash)))
                    logger.debug(
                        'Client {} broadcasting solution {} for block {}'.format(
                            self.name, solution.solution,
                            pretty_hash(solution.hash)))

                    self.blockchain.add_next(solution)
                    self.blockchain = solution

                    self.broadcast(data)
                else:
                    logger.warning(
                        'Client {} could not verify solution {} for block {}. '
                        'Ignoring solution'.format(
                            self.name, solution.solution,
                            pretty_hash(solution.hash)))

        else:
            # b_type is unrecognized by the client
            raise UnknownBroadcastType


def main():
    blockchain1 = Block()
    blockchain2 = Block()

    client1 = Client(name='client1', blockchain=blockchain1)
    broadcast_node_1 = LocalBroadcastNode(client1)
    client2 = Client(name='client2', blockchain=blockchain2,
                     broadcast_nodes=[broadcast_node_1])
    broadcast_node_2 = LocalBroadcastNode(client2)
    client1.broadcast_nodes.append(broadcast_node_2)

    print('Generated client with key: {}'.format(client1.key.exportKey()))

    transaction = Transaction(outputs={client2.addresses[0]: 20})
    print('Created transaction {}. Broadcasting it...'.format(pretty_hash(transaction.hash)))

    client1.broadcast_transaction(transaction)

    print('Mining the block...')
    solution = client2.mine_current_block()

    print('Block mined! Puzzle solution: {}'.format(solution))
    print('Gen transaction hash: {}'.format(
        pretty_hash(client2.current_block.gen_transaction.hash)))

    print('Client1 has {} coins'.format(client1.total_value()))
    print('Client2 has {} coins'.format(client2.total_value()))

    print('Client1 thinks Client2 has {} coins'.format(client1.total_value(client2.addresses)))
    print('Client2 thinks Client1 has {} coins'.format(client2.total_value(client1.addresses)))

    import pdb

    pdb.set_trace()


if __name__ == '__main__':
    sys.exit(main())

