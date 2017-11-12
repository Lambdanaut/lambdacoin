from Crypto.Hash import SHA
from Crypto.Random import random

import lambdacoin.constants


def generate_hash() -> str:
    """Generates a hash str"""
    return SHA.new(
        str(rando()).encode(
        lambdacoin.constants.STRING_ENCODING)).\
        hexdigest()


def rando():
    return random.StrongRandom().randint(2, 20000000)


def pretty_hash(hash: str) -> str:
    trailings = len(hash) // 8  # // is integer division in Python 3
    return '{}...{}'.format(hash[:trailings], hash[len(hash)-trailings:])
