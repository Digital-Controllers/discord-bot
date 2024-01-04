from pathlib import Path
from sys import executable, platform
import socket
import subprocess


__all__ = ["stop", "conn"]


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("localhost", 20250))

sock.listen(1)

process = subprocess.Popen([executable, Path(__file__).parent / "main.py"])

conn, addr = sock.accept()
conn.settimeout(3)

if platform == "win32":
    from signal import CTRL_C_EVENT

    def stop():
        process.send_signal(CTRL_C_EVENT)
        sock.close()
else:
    from signal import SIGINT

    def stop():
        process.send_signal(SIGINT)
        sock.close()
