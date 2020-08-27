import os
from PIL import Image
import mido
import sys
import nancarrow_player


# ------------------------------------------------------------------------
# ------------------------- GENERATE MIDI --------------------------------
# ------------------------------------------------------------------------
def generate_midifile_from_frames(framesfolder_name="greytest",
                                  output_midifile_name="output"):

    BEATS_PER_FRAME = 1

    PATH_FRAMES = os.getcwd() + f"/{framesfolder_name}/"
    FRAME_SIZE = (88, 64)
    DEFAULT_VELOCITY = 34

    # somewhat the midi resolution of a beat. I make sure is a multiplier fo
    # the height, so then the PIXEL_AS_TICKS is a integer
    TICKS_PER_BEAT = 8 * FRAME_SIZE[1]
    midi_file = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    # The default MIDI tempo is 120 BPM, and the default Time Signature is 4/4. so at 4 beats the bar
    # trying to set a frame as a bar
    PIXEL_AS_TICKS = (TICKS_PER_BEAT * BEATS_PER_FRAME) / FRAME_SIZE[1]

    print(
        f"TICKS_PER_BEAT: {TICKS_PER_BEAT} // PIXEL_AS_TICKS: {PIXEL_AS_TICKS}"
    )

    # midi_file = MidiFile()

    # tracks are NOT channels!!!!
    track = mido.MidiTrack()
    midi_file.tracks.append(track)
    # wtf is this
    # track.append(MetaMessage("set_tempo", time=6400))

    last_empty_rows_from_last_frame = 0
    # for frame_index, frame_name in enumerate(os.listdir(PATH_FRAMES)):
    for frame_index in range(100):
        frame_name = os.listdir(PATH_FRAMES)[0]

        frame_note = (frame_index % 88) + 20

        past_color_column_list = [None] * FRAME_SIZE[0]
        rows_without_changes = last_empty_rows_from_last_frame

        print(f"------------------ PROCESSING FRAME: {frame_index}")

        img = Image.open(PATH_FRAMES + frame_name)
        pix = img.load()

        delta_ticks = 0

        # i want 1 more, so i can close notes that end in the last pixel
        for y in range(FRAME_SIZE[1] + 1):

            if y != FRAME_SIZE[1]:
                rows_without_changes += 1
            delta_ticks = int(rows_without_changes * PIXEL_AS_TICKS)

            events_for_this_row = []

            for x in range(FRAME_SIZE[0]):
                note_start_y = 0
                last_pixel_color = past_color_column_list[x]

                if y == FRAME_SIZE[1]:
                    # this is y does not exist in the image. it just to close
                    # all notes that end in the last row
                    pixel_color = None
                else:
                    r, g, b, a = pix[x, FRAME_SIZE[1] - y - 1]
                    # grey = r * 0.3 + g * 0.59 + b * 0.11
                    grey = ((r + g + b) / 3) / 255

                    if grey <= 0.5:
                        pixel_color = 1
                    elif grey <= 0.9:
                        pixel_color = 2
                    else:
                        pixel_color = None

                    if grey <= 0.01:
                        pixel_color = 1
                    elif grey <= 0.35:
                        pixel_color = 2
                    elif grey <= 0.6:
                        pixel_color = 4
                    elif grey <= 0.95:
                        pixel_color = 8
                    else:
                        pixel_color = None

                note = x + 20
                if pixel_color != last_pixel_color:
                    rows_without_changes = 0

                    if pixel_color == None:
                        if int(frame_index % last_pixel_color) == 0:
                            events_for_this_row.append([
                                last_pixel_color, "note_off", note,
                                DEFAULT_VELOCITY
                            ])
                    else:
                        if int(frame_index % pixel_color) == 0:
                            events_for_this_row.append([
                                pixel_color, "note_on", note, DEFAULT_VELOCITY
                            ])

                        if last_pixel_color != None:
                            if int(frame_index % last_pixel_color) == 0:
                                events_for_this_row.append([
                                    last_pixel_color, "note_off", note,
                                    DEFAULT_VELOCITY
                                ])

                    past_color_column_list[x] = pixel_color

            # end for x
            for event in events_for_this_row:
                c_index, note_state, note_number, velocity = event
                print(
                    f"{c_index} : {note_state} : {note_number} : {delta_ticks}"
                )
                track.append(
                    mido.Message(note_state,
                                 channel=c_index,
                                 note=note_number,
                                 velocity=velocity,
                                 time=delta_ticks))
                # after adding one message with the delay for this row, the
                # delta is set to zero
                delta_ticks = 0

        # save last number of empty rows from this frame, to be uses as delay
        # in the notes of the next frame
        last_empty_rows_from_last_frame = rows_without_changes

    midi_file.save(f'{output_midifile_name}.mid')


# /////////////////////////////////////////////
# ----------------------------------------------------------
# ------------------------- MAIN ---------------------------
# ----------------------------------------------------------
if __name__ == "__main__":
    try:
        framesfolder_name = sys.argv[1]
    except:
        framesfolder_name = "stuttergreys"
    generate_midifile_from_frames(framesfolder_name)
    nancarrow_player.start("output.mid")
