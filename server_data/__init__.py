"""Interface between server_data process and main process"""
from sys import modules
from tb_multiprocessing.server_data import conn
from tb_multiprocessing.io_utils import network_decode, SocketHandler
from types import ModuleType


class ServerGetter(ModuleType):
    def __init__(self):
        super().__init__(__name__, 'Interface between server_data process and main process')
        self.connection = SocketHandler(conn)

    @property
    def gaw(self):
        data = network_decode(self.connection.read())
        return data[0]

    @property
    def pgaw(self):
        data = network_decode(self.connection.read())
        return data[1]

    @property
    def lkeu(self):
        data = network_decode(self.connection.read())
        return data[2]

    @property
    def lkna(self):
        data = network_decode(self.connection.read())
        return data[3]


modules[__name__] = ServerGetter()

