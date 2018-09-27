import asyncio
import pathlib
import ssl

import websockets
import logging
from uuid import uuid4

from Services.services import *
from Services.events import *

logging.basicConfig()


class Peer:

    # Beginning of Constructor
    def __init__(self, server_port, max_peers=None, my_id=None, server_host=None):
        self.debug = True
        self.server_port = int(server_port)
        self.protocol_version = "1.0.0"
        self.client_version = "Full-Node"
        self.server_socket = None
        self.__init_handlers()

        # If not supplied, the max_peers variable will be set up to 0
        # 0 value means unlimited peers
        if max_peers:
            self.max_peers = int(max_peers)
        else:
            self.max_peers = 0

        # If not supplied, the host name/IP address will be determined
        # by attempting to connect to a random host.
        if server_host:
            self.server_host = server_host
        else:
            self.__init_server_host()

        # If not supplied, the id' peer will be defined with unique identifier thanks to uuid
        if my_id:
            self.my_id = my_id
        else:
            self.__init_node_id()

        # Hash Table of connected peers
        self.peers = set()

    # End of Constructor

    def __init_handlers(self):
        self.handlers = {}
        self.handlers = {
            'PING': self.notify_pong,
            'HELLO': self.notify_handshaking,
            'GET_STATUS': self.notify_status,
            'GET_ADDR': self.notify_addr_broadcast
        }

    def __init_node_id(self):
        self.my_id = str(uuid4()).replace('-', '')

    def __init_server_host(self):
        self.server_host = get_ip()

    def __debug(self, msg):
        if self.debug:
            thread_debug(msg)

    async def notify_handshaking(self, websocket, data):
        if self.peers:
            message = handshaking_event(self.protocol_version, self.client_version, self.server_port, self.my_id)
            await websocket.send(message)

    async def notify_addr_broadcast(self, websocket, data):
        message = addr_event(self.server_host, self.server_port)
        await asyncio.wait([peer.send(message) for peer in self.peers])

    async def notify_status(self, websocket, data):
        if self.peers:
            message = status_event()
            await websocket.send(message)

    async def notify_ping(self, websocket, data):
        if self.peers:
            message = ping_event()
            await websocket.send(message)

    async def notify_pong(self, websocket, data):
        if self.peers:
            message = pong_event()
            await websocket.send(message)

    async def register_node(self, websocket):
        self.peers.add(websocket)
        await websocket.send(handshaking_event(self.protocol_version, self.client_version, self.server_port, self.my_id))

    def unregister_node(self, websocket):
        self.peers.remove(websocket)

    async def consumer(self, message, websocket):
        msg_type = None
        try:
            data = json.loads(message)
            print(data)
            if 'type' in data:
                if data['type']:
                    msg_type = data['type'].upper()
                if msg_type not in self.handlers:
                    logging.error(
                        "unsupported event: {}", data)
                else:
                    self.__debug('Handling peer msg: %s: %s' % (msg_type, data))
                    await self.handlers[msg_type](websocket, data)
            else:
                self.__debug("Need a 'type' key in every json message")
        except ValueError:
            self.__debug("Message need to respect Json Format")

    async def __consumer_handler(self, websocket, path):

        self.__debug('path: %s, peers_number: %s' % (path, len(self.peers)))
        self.__debug('Current Server Listening: %s (%s:%d)'
                     % (self.my_id, self.server_host, self.server_port))
        self.__debug('Listening for Connections on the open socket...')
        await self.register_node(websocket)
        try:
            async for message in websocket:
                await self.consumer(message, websocket)
        finally:
            self.unregister_node(websocket)

    def run_peer(self):

            self.__debug('Server started: %s (%s:%d)'
                         % (self.my_id, self.server_host, self.server_port))
            self.__debug('handlers size %s' % len(self.handlers))

            # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            # ssl_context.load_cert_chain(
            # pathlib.Path(__file__).with_name('localhost.pem'))

            self.server_socket = websockets.serve(self.__consumer_handler, self.server_host, self.server_port)
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(self.server_socket)
                loop.run_forever()
            except KeyboardInterrupt:
                print("Closing the server")
            loop.close()


peer = Peer(8081, 5)
peer.run_peer()