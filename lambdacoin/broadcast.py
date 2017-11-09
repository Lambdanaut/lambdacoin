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
