
from zk import ZK
import time

zk = ZK("192.168.100.20", port=4370)
conn = zk.connect()
print("Connected. Waiting for events...")

for att in conn.live_capture():
    print("EVENT:", att)
