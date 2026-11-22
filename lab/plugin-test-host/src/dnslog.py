# Logs each DNS query name received on 127.0.0.1:53 and answers REFUSED, so nothing resolves. Used by runapp.sh.
import socket, sys, time
out = open(sys.argv[1], 'a', buffering=1)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(('127.0.0.1', 53))
while True:
    data, addr = s.recvfrom(2048)
    i, labels = 12, []
    while i < len(data) and data[i]:
        n = data[i]; labels.append(data[i+1:i+1+n].decode('ascii', 'replace')); i += 1 + n
    qtype = int.from_bytes(data[i+1:i+3], 'big') if i + 3 <= len(data) else 0
    out.write(f"{time.strftime('%H:%M:%S')} {'.'.join(labels)} type={qtype}\n")
    resp = bytearray(data[:12]); resp[2] = 0x81; resp[3] = 0x85  # response, REFUSED
    s.sendto(bytes(resp) + data[12:i+5], addr)
