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



def build_song():
    song = []
    vertical = 64
    for f in range(10):
        frame = []
        for t in range(vertical):
            for n in range(1):
                note = 28 + f%2 * 6 + f%4 * 12 + f%2 * sine(f*0.025)*12
                channel = t
                start = (t/vertical+ f)
                end = (t/vertical+ f) + 0.01 + sine(t)*0.08 
                frame.append([
                    f, 
                    int(channel) % 10,
                    int(note) % 127, start%1, end%1, False, False
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