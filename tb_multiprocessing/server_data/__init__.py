from pathlib import Path
from signal import CTRL_C_EVENT
from sys import executable
import socket
import subprocess


__all__ = ['stop', 'conn']


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('localhost', 20250))

sock.listen(1)

process = subprocess.Popen([executable, Path(__file__).parent / "main.py"])

conn, addr = sock.accept()


def stop():
    process.send_signal(CTRL_C_EVENT)
    sock.close()
