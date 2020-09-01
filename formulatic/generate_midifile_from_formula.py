import math
import os
import sys
import mido
from PIL import Image


def generate_from_formula(formula, ticks_per_beat=64, *, output_path):
    midi_file = mido.MidiFile(ticks_per_beat=ticks_per_beat)

    # tracks are NOT channels!!!!
    track = mido.MidiTrack()
    midi_file.tracks.append(track)

    for t in range(ticks_per_beat * 4):
        for s in range(2):
            note_state = s
            note = int(60 + math.sin((t / 10)) * 30)
            velocity = 64
            delta_ticks = int((t % 20) + 1) * int((t / ticks_per_beat) * 100)

            channel = int(t % 3)

            if note_state == 1:
                note_state = "note_on"
            else:
                note_state = "note_off"

            track.append(
                mido.Message(note_state,
                             channel=channel,
                             note=note,
                             velocity=velocity,
                             time=delta_ticks))

    midi_file.save(output_path)


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