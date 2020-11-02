"""Small example OSC client

This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import argparse
import ast
import math
import random
import time

from pythonosc import udp_client


def sine(t):
    return math.sin(t) * 0.5 + 0.5


"""Ticks per beat"""
TPB = 64

# song = [[[4, 58, 0.234375, 0.265625, False, False],
#          [4, 71, 0.234375, 0.265625, False, False],
#          [4, 59, 0.21875, 0.28125, False, False],
#          [4, 70, 0.21875, 0.28125, False, False],
#          [4, 60, 0.2109375, 0.2890625, False, False],
#          [4, 69, 0.2109375, 0.2890625, False, False],
#          [4, 61, 0.203125, 0.296875, False, False],
#          [4, 62, 0.203125, 0.296875, False, False],
#          [4, 67, 0.203125, 0.296875, False, False],
#          [4, 68, 0.203125, 0.296875, False, False],
#          [4, 63, 0.1953125, 0.3046875, False, False],
#          [4, 64, 0.1953125, 0.3046875, False, False],
#          [4, 65, 0.1953125, 0.3046875, False, False],
#          [4, 66, 0.1953125, 0.3046875, False, False]],
#         [[4, 58, 0.734375, 0.765625, False, False],
#          [4, 71, 0.734375, 0.765625, False, False],
#          [4, 59, 0.71875, 0.78125, False, False],
#          [4, 70, 0.71875, 0.78125, False, False],
#          [4, 60, 0.7109375, 0.7890625, False, False],
#          [4, 69, 0.7109375, 0.7890625, False, False],
#          [4, 61, 0.703125, 0.796875, False, False],
#          [4, 62, 0.703125, 0.796875, False, False],
#          [4, 67, 0.703125, 0.796875, False, False],
#          [4, 68, 0.703125, 0.796875, False, False],
#          [4, 63, 0.6953125, 0.8046875, False, False],
#          [4, 64, 0.6953125, 0.8046875, False, False],
#          [4, 65, 0.6953125, 0.8046875, False, False],
#          [4, 66, 0.6953125, 0.8046875, False, False]]]
# song = []


def build_song():
    song = []
    for f in range(2):
        frame = []
        for t in range(64):
            for n in range(8):
                note = 30 + (t % 1) + sine(t) * 20
                channel = t
                start = (t / TPB + f)
                end = (t / TPB + f) + 3 / TPB
                frame.append([
                    int(channel) % 10,
                    int(note) % 127, start % TPB, end % TPB, False, False
                ])
        song.append(frame)
    return song


def write_song_and_refresh(song, *, host, port):
    client = udp_client.SimpleUDPClient(host, port)

    f = open("midi.txt", "w+")
    f.write(str(song))
    f.close()

    client.send_message("/refresh", None)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-H",
                        "--host",
                        default="127.0.0.1",
                        help="The host/ip of the OSC server")
    parser.add_argument("-P",
                        "--port",
                        type=int,
                        default=1337,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    song = build_song()
    write_song_and_refresh(song, host=args.host, port=args.port)