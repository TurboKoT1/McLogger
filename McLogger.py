from mcstatus import JavaServer
from twisted.internet import reactor
from quarry.net.proxy import ServerProtocol, ServerFactory, Bridge


class LoggerProtocol(ServerProtocol):
    bridge = None

    def setup(self):
        self.bridge = self.factory.bridge_class(self.factory, self)

    def player_joined(self):
        ServerProtocol.player_joined(self)
        self.bridge.downstream_ready()
        print(f"[CONNECT] * Player {self.display_name} joined to the server")

    def connection_lost(self, reason=None):
        ServerProtocol.connection_lost(self, reason)
        self.bridge.downstream_disconnected()

        if self.display_name is not None:
            print(f"[DISCONNECT] * Player {self.display_name} disconnected from the server")


class LoggerFactory(ServerFactory):
    protocol = LoggerProtocol


class LoggerBridge(Bridge):
    protocol = LoggerProtocol

    def packet_upstream_chat_message(self, buff):
        player_name = self.downstream.display_name
        buff.save()
        message = buff.unpack_string()
        print(f"[CHAT] * Player {player_name} sent message «{message}»")
        buff.restore()
        self.upstream.send_packet("chat_message", buff.read())

    def upstream_disconnected(self):
        self.downstream.close(self)


def start_logger(host: str, port: int) -> None:
    print('[SERVER] * Starting fake-server on 25565 port..')

    server = JavaServer.lookup(f"{host}:{port}")
    status = server.status()

    factory = LoggerFactory()
    factory.bridge_class = LoggerBridge
    factory.motd = status.description
    factory.max_players = status.players.max
    factory.icon = status.icon
    factory.online_mode = False
    factory.connect_host = host
    factory.connect_port = port
    factory.listen("127.0.0.1", 25565)

    reactor.run()


def get_args():
    while True:
        print("|| Enter address of the redirect server:")
        host = input("/> ")
        print("|| Enter port of the redirect server:")
        port = input("/> ")

        if not host or not host.strip():
            print("[ERROR] * Please enter a valid address.")
        elif not port.isdigit():
            print("[ERROR] * Please enter a valid port number.")
        else:
            start_logger(host, int(port))


def main(argv):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--host", default=None, help="address of redirect server")
    parser.add_argument("-p", "--port", default=25565, type=int, help="port of redirect server")
    args = parser.parse_args(argv)

    if args.host is not None:
        start_logger(args.host, args.port)
    else:
        get_args()


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
