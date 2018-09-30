import socket
import sys

import Peer


class App:

    def __init__(self):
        self.peer = Peer.Peer()

    def run(self):
        if (len(sys.argv) > 2 and sys.argv[2] == '-add_node') or len(self.peer.get_peers()) == 0:
            try:
                node = input('Enter address and port:')
            except SyntaxError:
                node = None
            if node is None or len(node) == 0:
                print("Address it not valid, no peer connected...")
            else:
                self.peer.add_node_discovery(node)
        if len(sys.argv) > 1:
            self.peer.server_port = int(sys.argv[1])
        self.peer.run_peer()


if __name__ == '__main__':
    app = App()
    app.run()
