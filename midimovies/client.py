"""Small example OSC client

This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import argparse
import random
import time
import ast
import math

from pythonosc import udp_client

def sine(t):
    return math.sin(t)*0.5+0.5

TPB = 64 #ticks per beat

song = [[[4, 58, 0.234375, 0.265625, False, False], [4, 71, 0.234375, 0.265625, False, False], [4, 59, 0.21875, 0.28125, False, False], [4, 70, 0.21875, 0.28125, False, False], [4, 60, 0.2109375, 0.2890625, False, False], [4, 69, 0.2109375, 0.2890625, False, False], [4, 61, 0.203125, 0.296875, False, False], [4, 62, 0.203125, 0.296875, False, False], [4, 67, 0.203125, 0.296875, False, False], [4, 68, 0.203125, 0.296875, False, False], [4, 63, 0.1953125, 0.3046875, False, False], [4, 64, 0.1953125, 0.3046875, False, False], [4, 65, 0.1953125, 0.3046875, False, False], [4, 66, 0.1953125, 0.3046875, False, False]], [[4, 58, 0.734375, 0.765625, False, False], [4, 71, 0.734375, 0.765625, False, False], [4, 59, 0.71875, 0.78125, False, False], [4, 70, 0.71875, 0.78125, False, False], [4, 60, 0.7109375, 0.7890625, False, False], [4, 69, 0.7109375, 0.7890625, False, False], [4, 61, 0.703125, 0.796875, False, False], [4, 62, 0.703125, 0.796875, False, False], [4, 67, 0.703125, 0.796875, False, False], [4, 68, 0.703125, 0.796875, False, False], [4, 63, 0.6953125, 0.8046875, False, False], [4, 64, 0.6953125, 0.8046875, False, False], [4, 65, 0.6953125, 0.8046875, False, False], [4, 66, 0.6953125, 0.8046875, False, False]]]
song = []
if __name__ == "__main__":

    song = []
    for f in range(4):
        
        frame = []
        for t in range(64):
            for n in range(4):
                note = 40+n + (t % 1) + sine(t)*1
                channel = t
                start = (t / TPB + f)
                end = (t / TPB + f) + 3/TPB

                frame.append([int(channel)%10, int(note)%127, start%TPB, end%TPB, False, False])

        song.append(frame)

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=1337,
        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    f= open("midi.txt","w+")
    f.write(str(song))
    f.close()

    client.send_message("/refresh", None)