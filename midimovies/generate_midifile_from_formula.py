import os
from PIL import Image
import mido
import sys
import math
import midimovies_player

def sine(t):
    return math.sin(t)*0.5+0.5

def generate_from_formula(formula, ticks_per_beat=64, *, output_path):
    midi_file = mido.MidiFile(ticks_per_beat=ticks_per_beat)

    # tracks are NOT channels!!!!
    track = mido.MidiTrack()
    midi_file.tracks.append(track)

    total_channels = 11

    for t in range(ticks_per_beat * 2):
        for s in range(1):
            for state in range(2):
                note_state = True if state == 0 else False
                note = 20 + (t % 88 - (s * sine(t / ticks_per_beat) * 80))
                channel = t / 100 + t % 88
                delta_ticks = int(t / ticks_per_beat) + 1

                velocity = 64
                if note_state:
                    note_state = "note_on"
                else:
                    note_state = "note_off"

                ticc = int(t / ticks_per_beat) + 1
                for clone in range(ticc):
                    new_note = int((note + clone) % 127)
                    channel = int(channel % total_channels)
                    track.append(
                        mido.Message(note_state,
                                     channel=channel,
                                     note=new_note,
                                     velocity=velocity,
                                     time=delta_ticks))
                    delta_ticks = 0

    midi_file.save(output_path)
    midimovies_player.start(output_path)
    

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a MIDI file from a formula",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f",
                        "--formula",
                        default=None,
                        help="formula expression")
    parser.add_argument("-o",
                        "--output",
                        help="output midi file",
                        default="formula.mid")
    parser.add_argument("--ticks-per-beat",
                        help="ticks per beat",
                        type=int,
                        default=8000)

    args = parser.parse_args()

    generate_from_formula(args.formula,
                          output_path=args.output,
                          ticks_per_beat=args.ticks_per_beat)


if __name__ == "__main__":
    main()