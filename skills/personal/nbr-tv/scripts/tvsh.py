#!/usr/bin/env python3
"""Run one command on the TV's root shell over telnet.

    python3 tvsh.py '<command>'

The TV runs telnetd as root with no password, started by the Homebrew Channel's boot script. Two
details shape this script: telnetd sends its greeting bytes before the prompt, and a command that
sleeps (waiting for an app to uninstall, say) leaves the socket silent for longer than a normal
timeout. It reads until the marker it appends to the command, so slow commands still print.
"""

import socket
import sys
import time

HOST = "192.168.2.117"
PORT = 23
DEADLINE = 200  # seconds; an app removal can take 30 per app


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    sock = socket.create_connection((HOST, PORT), timeout=6)
    sock.settimeout(10)
    time.sleep(1.0)
    try:
        sock.recv(8192)  # the greeting and the first prompt
    except OSError:
        pass
    sock.sendall(b"\n")
    time.sleep(0.5)
    sock.sendall(cmd.encode() + b'\necho "__END__$?"\n')

    buf = b""
    end = time.time() + DEADLINE
    while time.time() < end:
        try:
            chunk = sock.recv(8192)
        except socket.timeout:
            continue
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
        if b"__END__" in buf:
            break
    sock.close()

    # telnetd echoes the command back and wraps long lines, so cutting at the command loses the
    # answer. Print the session as it came, minus the carriage returns.
    text = buf.decode("utf-8", "replace").replace("\r", "")
    print(text.replace("__END__", "\n[exit] ").strip())


if __name__ == "__main__":
    main()
