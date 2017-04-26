from Crypto.Random import random


def rando():
    return random.StrongRandom().randint(2, 20000000)
