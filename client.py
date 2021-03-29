#!/usr/bin/env python3

import sys
import argparse
import socket
from sys import argv
import confundo


parser = argparse.ArgumentParser("Parser")
parser.add_argument("host", help="Set Hostname")
parser.add_argument("port", help="Set Port Number", type=int)
parser.add_argument("file", help="Set File Directory")
args = parser.parse_args()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if (len(argv) < 4) | (len(argv) > 4):
    sys.stderr.write("missing arguments or too many Arguments")
    sys.exit()

if (argv[1] == ""):
    sys.stderr.write("ERROR: empty string")
    sys.exit()
else:
    try:
        socket.gethostbyname(argv[1])
    except socket.error:
        sys.stderr.write("ERROR: wrong host")
        sys.exit()

if argv[2] == "":
    sys.stderr.write("ERROR: empty string")
    sys.exit()

if (int(argv[2]) < 0) | (int(argv[2]) > 65535):
    sys.stderr.write("ERROR: Overflow error")
    sys.exit()

file = open(args.file, "rb")


conn = confundo.Socket(sock)
try:
    remote = socket.getaddrinfo(args.host, args.port, family=socket.AF_INET, type=socket.SOCK_DGRAM)
except (socket.error, OverflowError) as e:
    sys.stderr.write("ERROR: Invalid hostname or port (%s)\n" % e)
    sock.close()
    sys.exit(1)

(family, type, proto, canonname, sockaddr) = remote[0]

# send "connect" (not fully connected yet)
conn.connect(sockaddr)

while True:
    try:
        (inPacket, fromAddr) = sock.recvfrom(1024)
        # Note in the above, parameter to .recvfrom should be at least MTU+12 (524), but can be anything else larger if we are willing to accept larger packets

        # Process incoming packet
        conn.on_receive(inPacket)

    except socket.error as e:
        # this is the source of timeouts
        isError = conn.on_timeout()
        if isError:
            # on_timout should return True on critical timeout
            sys.stderr.write("ERROR: (%s)\n" % e)
            sys.exit(1)
        if conn.isClosed():
            break

    while file and conn.canSendData():
        data = file.read(confundo.MTU)
        if not data:
            file = None
            break
        conn.send(data)

    if not file and conn.canSendData():
        conn.close()
