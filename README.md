Lambdacoin
==========


Proof of Work
-------------

Uses SHA hash function on transactions + nonce to get a hash. 

example:

abc3409jkgla4

When the nonce used generates an SHA hash that begins with x number of zeros, then the proof of work is satisfied. 

example of satisfactory hash where 4 zeros are required:

0000flaksjvior


Verification
------------

A block isn't verified until: 
(1) it is part of a block in the longest fork, and (2) at least 5 blocks follow it in the longest fork. In this case we say that the transaction has “6 confirmations”

Longest chain wins


Terminology
-----------

 * Gen Transaction: Reward transaction generated for a miner when a block is solved. Gen transactions have no inputs, just outputs.
 * UTXO: An Unspent Transaction Output (UTXO) that can be spent as an input in a new transaction.


Useful Resources
----------------

* Bitcoin developer guide: https://bitcoin.org/en/developer-guide