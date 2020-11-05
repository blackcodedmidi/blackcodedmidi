import os
from PIL import Image
import mido
import sys


# ------------------------------------------------------------------------
# ------------------------- GENERATE MIDI --------------------------------
# ------------------------------------------------------------------------
def duplicateFirstFrameAtTheEnd(song):
    number_of_frames = len(song)

    cloned_first_frame = []

    for note in song[0]:  # for notes in first frame
        new_note = note.copy()
        new_note[0] = number_of_frames
        cloned_first_frame.append(new_note)
    song.append(cloned_first_frame)
    return song
def generate_list_from_midifile(midifile):
    TOTAL_NOTES = 127
    NUMBER_OF_CHANNELS = 16
    # --------------------------------------------------------
    # -----------  OPEN MIDI FILE AND PROCESS IT --------
    # ---------------------------------------------------------
    # open midifile and start to format to handy lists
    mid = mido.MidiFile(f"{midifile}.mid")
    song = []
    start_times = []
    for c in range(NUMBER_OF_CHANNELS):
        start_times.append([None] * TOTAL_NOTES)
    timer = 0
    frame_data = []
    frame_timer = 0
    # formatea la data midi a algo con menos cancer. para que cada nota tenga
    # su start y end
    print("STARTING RECONVERTING MIDIFILE TO SOMETHING MORE HANDY")
    # default midi is 120 BPM
    FRAME_AS_SECONDS = 60 / 60
    current_frame = 0
    for i, msg in enumerate(mid):
        if not isinstance(msg, mido.MetaMessage):
            # msg.time come as seconds
            timer += msg.time
            frame_timer += msg.time

            if frame_timer > FRAME_AS_SECONDS:  # it's a new film frame!
                current_frame += 1
                # grab the extra time that pass since the start of this new
                # frame
                frame_timer = frame_timer - FRAME_AS_SECONDS
                # add frame to the song
                song.append(frame_data)
                frame_data = []

            if (msg.type == "note_on"):
                # print("ON")
                # print(f"save time on channel {msg.channel}:{msg.note} =
                # {timer}")
                start_times[msg.channel][msg.note] = frame_timer
            elif (msg.type == 'note_off'):
                # print("OFF")
                start = start_times[msg.channel][msg.note]
                end = frame_timer
                data = [
                    current_frame, msg.channel, msg.note, 64, start, end, False,
                    False
                ]
                # print(data)
                frame_data.append(data)
    #don't forget to add the last frame!
    song.append(frame_data)

    # Check what is inside of this new data
    # for frame_index, frame in enumerate(song):
    #     print(f"---- {frame_index}")
    #     for m in frame:
    #         print(m)
    # quit()

    if True: #LOOP_GLUE
        song = duplicateFirstFrameAtTheEnd(song)

    # print(song)
    # print(f"TOTAL_FRAMES: {TOTAL_FRAMES}")
    f = open(f"{midifile}.txt", "w+")
    f.write(str(song))
    f.close()

    print("DONE CONVERTING MIDIFILE")
def generate_midifile_from_frames(framesfolder_name="test2", output_midifile_name="output", nancarrow=True, clone_multiplier=1):

    MODE_NANCARROW = nancarrow

    # this was originally 1, but with two works with the new player that expects 1 as a complete height of the window
    BEATS_PER_FRAME = 2

    PATH_FRAMES = os.getcwd() + f"/movies_as_frames/{framesfolder_name}/"
    FRAME_SIZE = (88, 64)
    DEFAULT_VELOCITY = 34

    TICKS_PER_BEAT = 8 * FRAME_SIZE[1] #somewhat the midi resolution of a beat. I make sure is a multiplier fo the height, so then the PIXEL_AS_TICKS is a integer
    midi_file = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    # The default MIDI tempo is 120 BPM, and the default Time Signature is 4/4. so at 4 beats the bar
    # trying to set a frame as a bar
    PIXEL_AS_TICKS = (TICKS_PER_BEAT * BEATS_PER_FRAME) / FRAME_SIZE[1]

    print(f"TICKS_PER_BEAT: {TICKS_PER_BEAT} // PIXEL_AS_TICKS: {PIXEL_AS_TICKS}")

    # midi_file = MidiFile()

    # tracks are NOT channels!!!!
    track = mido.MidiTrack()
    midi_file.tracks.append(track)
    # wtf is this
    # track.append(MetaMessage("set_tempo", time=6400))

    last_empty_rows_from_last_frame = 0
    frames_in_directory = os.listdir(PATH_FRAMES)

    # clone_multiplier hack
    # the idea is to makes as there is more frames that they really are. 
    # its usefull for testing as let have only one png file in the frame folder, without triggering the "end of the pianoroll" every frame
    frames_to_process = []
    for i in range(len(frames_in_directory) * clone_multiplier):
    	index = i % len(frames_in_directory)
    	frames_to_process.append(frames_in_directory[index])

    print(frames_to_process)

    for frame_index, frame_name in enumerate(frames_to_process):

        frame_note = (frame_index % 88) + 20
        
        past_color_column_list = [None] * FRAME_SIZE[0]
        rows_without_changes = last_empty_rows_from_last_frame

        print(f"PROCESSING FRAME: {frame_index} / {len(frames_to_process)}")

        img = Image.open(PATH_FRAMES + frame_name)
        pix = img.load()

        delta_ticks = 0

        # I want 1 more, so i can close notes that end in the last pixel
        for y in range(FRAME_SIZE[1]+1):      

            # y = FRAME_SIZE[1]+1 - y
            
            if y != FRAME_SIZE[1]:
                rows_without_changes += 1
            delta_ticks = int(rows_without_changes*PIXEL_AS_TICKS)

            events_for_this_row = []

            for x in range(FRAME_SIZE[0]):
                note_start_y = 0
                last_pixel_color = past_color_column_list[x]

                if y == FRAME_SIZE[1]:
                    # this is y does not exist in the image. it just to close all notes that end in the last row
                    pixel_color = None
                else:
                    color_channels = pix[x, FRAME_SIZE[1] - y - 1]
                    r, g, b = color_channels[0], color_channels[1], color_channels[2]
                                       

                    if MODE_NANCARROW:
                        grey = ((r + g + b) / 3)/255


                        if grey >= 0.9:
                            pixel_color = None
                        elif grey <= 0.2:
                            pixel_color = 1
                        elif grey <= 0.6:
                            pixel_color = 2
                        else:
                            pixel_color = 3

                        # if grey <= 0.01:
                        #     pixel_color = 1
                        # elif grey <= 0.35:
                        #     pixel_color = 2
                        # elif grey <= 0.6:
                        #     pixel_color = 4
                        # elif grey <= 0.95:
                        #     pixel_color = 8
                        # else:
                        #     pixel_color = None

                    else:
                        grey = r * 0.3 + g * 0.59 + b * 0.11

                        if r > 100:
                            if g > 100:
                                pixel_color = 3
                            else:
                                pixel_color = 0
                        elif g > 100:
                            pixel_color = 1
                        elif b > 100:
                            pixel_color = 2
                        else:
                            pixel_color = None

                                                
                        # # for betty boop
                        # if grey < 20:
                        # 	pixel_color = None
                        # elif grey < 65:
                        # 	pixel_color = 0
                        # elif grey < 90:
                        #     pixel_color = 1
                        # elif grey < 145:
                        #     pixel_color = 2
                        # elif grey < 200:
                        #     pixel_color = 3
                        # else:
                        #     pixel_color = 4

                note = x + 20
                if pixel_color != last_pixel_color:
                    rows_without_changes = 0

                    if pixel_color == None:
                        if not MODE_NANCARROW or int(frame_index % last_pixel_color) == 0:
                            events_for_this_row.append([last_pixel_color, "note_off", note, DEFAULT_VELOCITY])
                    else:
                        if not MODE_NANCARROW or int(frame_index % pixel_color) == 0:
                            events_for_this_row.append([pixel_color, "note_on", note, DEFAULT_VELOCITY])
                    
                        if last_pixel_color != None:
                            if not MODE_NANCARROW or int(frame_index % last_pixel_color) == 0:
                                events_for_this_row.append([last_pixel_color, "note_off", note, DEFAULT_VELOCITY])


                    past_color_column_list[x] = pixel_color 

            # end for x
            for event in events_for_this_row:
                c_index, note_state, note_number, velocity = event
                print(f"{c_index} : {note_state} : {note_number} : {delta_ticks}")
                track.append(mido.Message(note_state, channel=c_index, note=note_number, velocity=velocity, time=delta_ticks))
                delta_ticks = 0 # after adding one message with the delay for this row, the delta is set to zero

        #save last number of empty rows from this frame, to be uses as delay in the notes of the next frame
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
        framesfolder_name = "test-simple"
    generate_midifile_from_frames(framesfolder_name, nancarrow=False, clone_multiplier=1, output_midifile_name=framesfolder_name)
    generate_list_from_midifile(framesfolder_name)