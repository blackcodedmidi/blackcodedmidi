import os
import mido
import mido.backends.rtmidi  # explicit import for when building the .exe
import pygame
import pygame.freetype  # Import the freetype module.
import math
import time


# ------------------------------------------------------------------------
# ------------------------- PLAYER ---------------------------------------
# ------------------------------------------------------------------------
def loopy_index(array, index):
    length = len(array)

    if index >= length:
        index = index - length
    elif index < 0:
        index = length - index

    index = index % length
    return array[index]

def start(midifile_name="output.mid", nancarrow=False, output_device=None):
    MODE_NANCARROW = nancarrow
    OPTIONS_SAVEFRAMES = False
    OPTIONS_SENDMIDI = True
    AUTOMATIC_ACCELERATION = False

    BEATS_PER_FRAME = 1
    TOTAL_NOTES = 127
    NUMBER_OF_CHANNELS = 16


    # Open the first output, by default
    if not output_device:
        outputs = mido.get_output_names()
        print("Available MIDI outputs:", outputs)
        output_device = outputs[0]

    print("MIDI output:", output_device)
    _midiport_ = mido.open_output(output_device)


    # --------------------------------------------------------
    # -----------  OPEN MIDI FILE AND PROCESS IT --------
    # ---------------------------------------------------------
    # open midifile and start to format to handy lists
    mid = mido.MidiFile(midifile_name)
    song = []
    # TODO: needs a more procedural way of populing this bois...
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
    FRAME_AS_SECONDS = 60 / 120
    for i, msg in enumerate(mid):
        if not isinstance(msg, mido.MetaMessage):
            # msg.time come as seconds
            timer += msg.time
            frame_timer += msg.time

            if frame_timer > FRAME_AS_SECONDS:  # it's a new film frame!
                # grab the extra time that pass since the start of this new
                # frame
                frame_timer = frame_timer - FRAME_AS_SECONDS
                # add frame to the song
                song.append(frame_data)
                frame_data = []

            if(msg.type == "note_on"):
                # print(f"save time on channel {msg.channel}:{msg.note} =
                # {timer}")
                start_times[msg.channel][msg.note] = timer
            elif(msg.type == 'note_off'):
                start = start_times[msg.channel][msg.note]
                end = timer
                data = [msg.channel, msg.note, start, end, False, False]
                frame_data.append(data)
    # Check what is inside of this new data
    # for frame_index, frame in enumerate(song):
    #     print(f"---- {frame_index}")
    #     for m in frame:
    #         print(m)
    # quit()
    print("DONE CONVERTING MIDIFILE")
    # -----------------------------------------------------------------



    # --------------------------------------------------------
    # ---------------- COLORES ----------------------------
    # --------------------------------------------------------
    # Define some colors, and what color is used for every channel
    COLOR_BLACK = (0, 0, 0)
    COLOR_RED = (255, 0, 0)
    COLOR_GREEN = (0, 255, 0)
    COLOR_BLUE = (0, 0, 255)
    COLOR_YELLOW = (255, 255, 0)
    COLOR_WHITE = (255, 255, 255)
    COLOR_HOLE = (0, 0, 0)

    # nice palette for N64 logo
    
    # paleta arcoiris hipster
    COLOR_CHANNELS = [
        (4, 84, 89),
        (8, 115, 83),
        (21, 194, 134),
        (171, 217, 109),
        (251, 191, 84),
        (238, 107, 59),
        (236, 15, 71),
        (160, 44, 93),
        (112, 4, 96),
        (2, 44, 122),
        (38, 41, 73),
    ]

    # le queda cheto a betty boop
    COLOR_CHANNELS = [
        (62, 14, 69),
        (76, 94, 176),
        (126, 169, 141),
        (172, 215, 153),
        (218, 237, 210),
        (255, 255, 255),
    ]



    # COLOR_CHANNELS = [COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW]
    # nice palette for black n white movies
    # COLOR_CHANNELS = [(50, 50, 50), (100, 100, 100),(150, 150, 150), (200, 200, 200)]

    # fill the rest of the channels with a default color, becouse later COLOR_CHANNELS is expexted to be the same length that NUMBER_OF_CHANNELS
    COLOR_CHANNELS = COLOR_CHANNELS + list([COLOR_WHITE]*(NUMBER_OF_CHANNELS-len(COLOR_CHANNELS)))
    # --------------------------------------------------------


    # ----------------------------------------
    # start pygame and create a lot of variables that will be used on the game loop TODO: better naming and less magic numbers pleaseeeee
    # ----------------------------------------
    pygame.init()
    FPS = 60
    EXIT = False
    scroller_y = 0
    MIDINOTE_OFFSET = 20  # first 20 midinotes are silent
    # for drawing the bottom piano keys
    BLACKS_PATTERN = [False, True, False, True, False, False, True, False, True, False, True, False]

    if MODE_NANCARROW:
        BARGFX_WIDTH = 7
        BARGFX_MARGIN = 5
        WINDOWS_SIZE = (1024, 600)
        SOUND_TRIGGER_ZONE = 0
    else:
        BARGFX_WIDTH = 9
        BARGFX_MARGIN = 1
        WINDOWS_SIZE = (878, 600)
        SOUND_TRIGGER_ZONE = int(WINDOWS_SIZE[1] / 10)
    WINDOW_WIDTH = WINDOWS_SIZE[0]
    WINDOW_HEIGHT = WINDOWS_SIZE[1]



    FONT_LOG = pygame.freetype.Font("assets/consola.ttf", 18)
    screen = pygame.display.set_mode(WINDOWS_SIZE)
    pygame.display.set_caption("MidiMovies")
    pygame_clock = pygame.time.Clock()


    FRAMEHEIGHT_AS_SECONDS = BEATS_PER_FRAME / (120 / 60)  # default for created midis is 120 BPM    

    TOTAL_FRAMES = math.ceil(mid.length / FRAMEHEIGHT_AS_SECONDS)

    channels_notes_isplaying = []
    for i in range(NUMBER_OF_CHANNELS):
        temp_notes_state = []
        for n in range(TOTAL_NOTES):
            temp_notes_state.append(False)
        channels_notes_isplaying.append(temp_notes_state)


    # LOADING SOME SPRITES (only for nancarrow really)
    if MODE_NANCARROW:
        # not used for now
        # spr_hole_start = pygame.image.load('assets/hole_start.png')
        # spr_hole_middle = pygame.image.load('assets/hole_middle.png')
        # spr_hole_end = pygame.image.load('assets/hole_end.png')
        # spr_hole_complete = pygame.image.load('assets/hole_complete.png')
        spr_canvas = pygame.image.load('assets/canvas.png')

    # for keep track of updates and save screenshots of the window
    pygame_update_counter = 0

    # ------------------------------------------------------
    # MAIN GAME LOOP! ALL SOUND and DRAWING happens here
    # ------------------------------------------------------
    time_started_at = time.time()
    while not EXIT:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                EXIT = True

        speed = 0       
        if AUTOMATIC_ACCELERATION:

            t = time.time() - time_started_at

            if t <= 20:
                speed = abs(math.sin((t/20) * (math.pi/2)))
            elif t < 30:
                speed = 1
            else:
                speed = 1-abs(math.sin(((t-30)/20) * (math.pi/2)))

            # print(f"t: {round(t, 1)} speed:{round(speed, 2)}")

            speed = speed * WINDOW_HEIGHT * 0.99

        else:  # CHECK MOUSE INPUT, SET PLAYING SPEED, AND CALCULATE WHERE WHE ARE IN THE PIANO ROLL
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # scroller_y += ((mouse_y- WINDOW_HEIGHT/2)/WINDOW_HEIGHT/2)*50
            speed = WINDOW_HEIGHT*(mouse_y/WINDOW_HEIGHT)*1.01
            # speed = WINDOW_HEIGHT*(0.2)*1.01

            
        scroller_y += speed
        if scroller_y > WINDOW_HEIGHT*TOTAL_FRAMES:
            scroller_y = 0
        elif scroller_y < 0:
            scroller_y = WINDOW_HEIGHT*TOTAL_FRAMES

        # clean screen
        if MODE_NANCARROW:
            # canvas is 2400 height
            # screen.blit(spr_canvas, (0, int(scroller_y%1200) - 1800))
            screen.fill(COLOR_WHITE)
        else:
            screen.fill(COLOR_BLACK)


        # grab in wich "frame" of the movie whe are TODO: is this correct? Also, the last frame don't show
        position_in_frames = int(scroller_y/WINDOW_HEIGHT)
        # grabing just the frames that that have a chance of drawing or making sound in this iteration
        notes_to_check = []
        notes_to_check += loopy_index(song, position_in_frames-1)
        notes_to_check += loopy_index(song, position_in_frames)
        notes_to_check += loopy_index(song, position_in_frames+1)

        for note in notes_to_check:

            # fail safe check, skip note if it has something weird
            baddata = False
            for d in note:
                if d is None:
                    baddata = True
            if baddata:
                continue

            # converting note's start and end values to screen's height porcentage
            x = (note[1]-MIDINOTE_OFFSET)*(BARGFX_WIDTH + BARGFX_MARGIN)
            start = (note[2]/FRAMEHEIGHT_AS_SECONDS) * WINDOW_HEIGHT
            end = (note[3]/FRAMEHEIGHT_AS_SECONDS) * WINDOW_HEIGHT
            # print(f"start {start} / end {end}")

            #----- DRAW NOTE
            if (start > scroller_y and start < scroller_y+WINDOW_HEIGHT) or (end > scroller_y and end < scroller_y+WINDOW_HEIGHT):
                # print(f"{x} {end - start}")
                # pygame.draw.rect(screen, COLOR_WHITE, (x, start, x+BARGFX_WIDTH, end), 0)
                x = int(x)
                y = int(WINDOW_HEIGHT - (end - scroller_y))
                w = int(BARGFX_WIDTH)
                h = int((end-start))
                

                if MODE_NANCARROW:
                    # screen.blit(spr_hole_start, (x, y + h))
                    # for _y in range(h):
                    #     screen.blit(spr_hole_start, (x, y + h))
                    # screen.blit(spr_hole_end, (x, y))

                    pygame.draw.rect(screen, COLOR_HOLE, (x, y, w, h), 0)
                    pygame.draw.ellipse(screen, COLOR_HOLE, (x, y-w/2, w, w), 0)
                    pygame.draw.ellipse(screen, COLOR_HOLE, (x, y+h-w/2, w, w), 0)
                else:
                    pygame.draw.rect(screen, COLOR_CHANNELS[note[0]], (x, y, w, h), 0)


            #----- SEND MIDI
            if OPTIONS_SENDMIDI:
                # TODO: this could be clearer.
                # Main idea is that note[4] is True is the note has already started playing
                # and note[5] is True is the note has already trigger its end state
                # This was for something like stoping the sound to trigger itself multiple times, or something like that.
                if note[4] == False:
                    if start < scroller_y+SOUND_TRIGGER_ZONE:
                        note[4] = True
                        channels_notes_isplaying[note[0]][note[1]] = True # I think this is used only for the drawing of the piano keys at bottom
                        msg = mido.Message("note_on", channel=note[0], note=note[1])
                        # actually send midi message
                        _midiport_.send(msg)
                elif note[5] == False:
                    if end < scroller_y+SOUND_TRIGGER_ZONE:
                        note[5] = True
                        channels_notes_isplaying[note[0]][note[1]] = False
                        msg = mido.Message("note_off", channel=note[0], note=note[1])
                        _midiport_.send(msg)
                elif start > scroller_y+SOUND_TRIGGER_ZONE and end > scroller_y+SOUND_TRIGGER_ZONE:
                    # This resets the triggering ability of the notes, when the pianoroll loops, and the movie start again
                    note[4] = False
                    note[5] = False

        # DRAW TINY PIANO KEYS GUI AT THE BOTTOM, And color the ones that are 'hold'
        if not MODE_NANCARROW:
            for piano_key in range(TOTAL_NOTES):
                color = None  
                for channel_index in range(NUMBER_OF_CHANNELS):
                    current_channel = channels_notes_isplaying[channel_index]
                    if current_channel[piano_key] == True:
                        if MODE_NANCARROW:
                            color = COLOR_HOLE
                        else:
                            color = COLOR_CHANNELS[channel_index]
                if not color:
                    if BLACKS_PATTERN[piano_key%12]:
                        color = COLOR_BLACK
                    else:
                        color = COLOR_WHITE
                pygame.draw.rect(screen, color, (int((piano_key-MIDINOTE_OFFSET)*(BARGFX_WIDTH + BARGFX_MARGIN)), int(WINDOW_HEIGHT-SOUND_TRIGGER_ZONE), BARGFX_WIDTH, SOUND_TRIGGER_ZONE), 0)
            pygame.draw.line(screen, COLOR_WHITE, (0, int(WINDOW_HEIGHT-SOUND_TRIGGER_ZONE)), (WINDOW_WIDTH, int(WINDOW_HEIGHT-SOUND_TRIGGER_ZONE)), 2)
        
        # SHOW SOME STATS
        if not OPTIONS_SAVEFRAMES:
            BPM = (speed/WINDOW_HEIGHT)*FPS*60
            FONT_LOG.render_to(screen, (10, 10), f"BPM:{int(BPM)}", COLOR_WHITE)
            FONT_LOG.render_to(screen, (10, 30), f"FPS:{int(pygame_clock.get_fps())}", COLOR_WHITE)
        # update the window screen with all the new drawings
        pygame.display.flip()
        # --- Limit to 60 frames per second. TODO: 60FPS is really the max FPS in pygame?
        pygame_clock.tick(FPS)
        if OPTIONS_SAVEFRAMES:
            pygame_update_counter += 1
            pygame.image.save(screen, f"pygame_record/frame_{str(pygame_update_counter).zfill(6)}.png")

    # Close the window and quit.
    pygame.quit()
# /////////////////////////////////////////////


# ----------------------------------------------------------
# ------------------------- MAIN ---------------------------
# ----------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Play a MIDI file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m",
                        "--midifile",
                        default="formula.mid",
                        help="MIDI file to play")
    parser.add_argument("--nancarrow",
                        dest="nancarrow",
                        action="store_true",
                        help="enable Nancarrow mode",
                        default=False)
    parser.add_argument("--no-nancarrow",
                        dest="nancarrow",
                        action="store_false",
                        help="disable Nancarrow mode")
    parser.add_argument('--output-device',
                        '-o',
                        default='OmniMIDI 1',
                        help='MIDI output device')

    args = parser.parse_args()

    start(args.midifile,
          nancarrow=args.nancarrow,
          output_device=args.output_device)


if __name__ == "__main__":
    main()