from Crypto.Random import random


def rando():
    return random.StrongRandom().randint(2, 20000000)

def pretty_hash(hash):
    trailings = len(hash) / 8
    return '{}...{}'.format(hash[:trailings], hash[len(hash)-trailings:])
