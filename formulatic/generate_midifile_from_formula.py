import os
from PIL import Image
import mido
import sys
import math




TICKS_PER_BEAT = 8000 #somewhat the midi resolution of a beat. I make sure is a multiplier fo the height, so then the PIXEL_AS_TICKS is a integer
midi_file = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)


# tracks are NOT channels!!!!
track = mido.MidiTrack()
midi_file.tracks.append(track)

for t in range(TICKS_PER_BEAT*4):
    for s in range(2):
        note_state = s
        note = 20 + t%88
        velocity = 64
        delta_ticks = 20

        channel = int(t%3)

        if note_state == 1:
            note_state = "note_on"
        else:
            note_state = "note_off"

        track.append(mido.Message(note_state, channel=channel, note=note, velocity=velocity, time=delta_ticks))


midi_file.save("formula.mid")
