# Broadcast Exceptions
class BroadcastError(Exception):
    pass


class UnknownBroadcastType(BroadcastError):
    pass


# Message Parsing Exceptions
class ParseMessageError(Exception):
    pass
