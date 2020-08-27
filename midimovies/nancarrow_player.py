import math
import os

import mido
import mido.backends.rtmidi  # explicit import for when building the .exe
import pygame
import pygame.freetype  # Import the freetype module.

print(mido.get_output_names())

OPTIONS_SENDMIDI = True
OPTIONS_SAVEFRAMES = False


# quit()
# ------------------------------------------------------------------------
# ------------------------- PLAYER ---------------------------------------
# ------------------------------------------------------------------------
def start(midifile_name="output.mid"):

    BEATS_PER_FRAME = 1

    TOTAL_NOTES = 127

    _midiport_ = mido.open_output('OmniMIDI 1')

    mid = mido.MidiFile(midifile_name)
    song = []

    start_times = [[None] * TOTAL_NOTES, [None] * TOTAL_NOTES,
                   [None] * TOTAL_NOTES, [None] * TOTAL_NOTES,
                   [None] * TOTAL_NOTES, [None] * TOTAL_NOTES,
                   [None] * TOTAL_NOTES, [None] * TOTAL_NOTES,
                   [None] * TOTAL_NOTES, [None] * TOTAL_NOTES,
                   [None] * TOTAL_NOTES]

    timer = 0
    # formatea la data midi a algo con menos cancer. para que cada nota tenga su start y end
    for msg in mid:
        # print(msg)
        if not isinstance(msg, mido.MetaMessage):
            # msg.time come as seconds
            # timer += mido.second2tick(msg.time, mid.ticks_per_beat, 500000)
            timer += msg.time

            # print(timer)
            if (msg.type == "note_on"):
                # print(f"save time on channel {msg.channel}:{msg.note} = {timer}")
                start_times[msg.channel][msg.note] = timer
            elif (msg.type == 'note_off'):
                start = start_times[msg.channel][msg.note]
                end = timer
                data = [msg.channel, msg.note, start, end, False, False]
                # print(data)
                song.append(data)

    # for s in song:
    #     print(s)
    # quit()

    # Define some colors
    COLOR_BLACK = (0, 0, 0)
    COLOR_RED = (255, 0, 0)
    COLOR_GREE = (0, 255, 0)
    COLOR_BLUE = (0, 0, 255)
    COLOR_YELLOW = (255, 255, 0)
    COLOR_WHITE = (255, 255, 255)

    COLOR_HOLE = (83, 65, 43)

    # COLOR_CHANNELS = [COLOR_RED, COLOR_GREE, COLOR_BLUE, COLOR_YELLOW]
    COLOR_CHANNELS = [(0, 0, 0), (64, 64, 64), (128, 128, 128),
                      (172, 172, 172), (255, 255, 255)]

    # start pygame
    pygame.init()
    FPS = 60
    WINDOWS_SIZE = (878, 600)
    WINDOW_WIDTH = WINDOWS_SIZE[0]
    WINDOW_HEIGHT = WINDOWS_SIZE[1]
    FONT_LOG = pygame.freetype.Font("consola.ttf", 18)
    screen = pygame.display.set_mode(WINDOWS_SIZE)
    pygame.display.set_caption("MidiMovies")

    EXIT = False
    pygame_clock = pygame.time.Clock()

    BARGFX_WIDTH = 9
    BARGFX_MARGIN = 1
    MIDINOTE_OFFSET = 20  #first 20 midinotes are silent

    scroller_y = 0

    #default for created midis is 120 BPM
    FRAMEHEIGHT_AS_SECONDS = BEATS_PER_FRAME / (120 / 60)
    SOUND_TRIGGER_ZONE = WINDOW_HEIGHT / 10
    TOTAL_FRAMES = math.ceil(mid.length / FRAMEHEIGHT_AS_SECONDS)

    TOTAL_CHANNELS = len(COLOR_CHANNELS)

    channels_notes_isplaying = []
    for i in range(10):
        temp_notes_state = []
        for n in range(TOTAL_NOTES):
            temp_notes_state.append(False)
        channels_notes_isplaying.append(temp_notes_state)

    BLACKS_PATTERN = [
        False, True, False, True, False, False, True, False, True, False, True,
        False
    ]

    spr_hole_start = pygame.image.load('hole_start.png')
    spr_hole_middle = pygame.image.load('hole_middle.png')
    spr_hole_end = pygame.image.load('hole_end.png')
    spr_hole_complete = pygame.image.load('hole_complete.png')

    spr_canvas = pygame.image.load('canvas.png')

    frame_counter = 0

    while not EXIT:
        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                EXIT = True

        # screen.fill(COLOR_WHITE)
        # canvas is 2400 height
        screen.blit(spr_canvas, (0, int(scroller_y % 1200) - 1800))

        for note in song:

            baddata = False
            for d in note:
                if d is None:
                    baddata = True

            if baddata:
                continue

            x = (note[1] - MIDINOTE_OFFSET) * (BARGFX_WIDTH + BARGFX_MARGIN)
            start = (note[2] / FRAMEHEIGHT_AS_SECONDS) * WINDOW_HEIGHT
            end = (note[3] / FRAMEHEIGHT_AS_SECONDS) * WINDOW_HEIGHT
            # print(f"start {start} / end {end}")

            #draw
            if (start > scroller_y and start < scroller_y + WINDOW_HEIGHT) or (
                    end > scroller_y and end < scroller_y + WINDOW_HEIGHT):
                # print(f"{x} {end - start}")
                # pygame.draw.rect(screen, COLOR_WHITE, (x, start, x+BARGFX_WIDTH, end), 0)
                x = int(x)
                y = int(WINDOW_HEIGHT - (end - scroller_y))
                w = int(BARGFX_WIDTH)
                h = int((end - start))

                # screen.blit(spr_hole_start, (x, y + h))
                # for _y in range(h):
                #     screen.blit(spr_hole_start, (x, y + h))
                # screen.blit(spr_hole_end, (x, y))

                pygame.draw.rect(screen, COLOR_HOLE, (x, y, w, h), 0)
                pygame.draw.ellipse(screen, COLOR_HOLE, (x, y - w / 2, w, w),
                                    0)
                pygame.draw.ellipse(screen, COLOR_HOLE,
                                    (x, y + h - w / 2, w, w), 0)

            # sound
            if OPTIONS_SENDMIDI:
                if note[4] == False:
                    if start < scroller_y + SOUND_TRIGGER_ZONE:
                        note[4] = True
                        channels_notes_isplaying[note[0]][note[1]] = True
                        msg = mido.Message("note_on",
                                           channel=note[0],
                                           note=note[1])
                        _midiport_.send(msg)
                elif note[5] == False:
                    if end < scroller_y + SOUND_TRIGGER_ZONE:
                        note[5] = True
                        channels_notes_isplaying[note[0]][note[1]] = False
                        msg = mido.Message("note_off",
                                           channel=note[0],
                                           note=note[1])
                        _midiport_.send(msg)
                elif start > scroller_y + SOUND_TRIGGER_ZONE and end > scroller_y + SOUND_TRIGGER_ZONE:
                    note[4] = False
                    note[5] = False

        for piano_key in range(TOTAL_NOTES):
            color = None
            for channel_index in range(TOTAL_CHANNELS):
                current_channel = channels_notes_isplaying[channel_index]
                if current_channel[piano_key] == True:
                    color = COLOR_CHANNELS[channel_index]
            if not color:
                if BLACKS_PATTERN[piano_key % 12]:
                    color = COLOR_BLACK
                else:
                    color = COLOR_WHITE
            pygame.draw.rect(
                screen, color,
                ((piano_key - MIDINOTE_OFFSET) *
                 (BARGFX_WIDTH + BARGFX_MARGIN), WINDOW_HEIGHT -
                 SOUND_TRIGGER_ZONE, BARGFX_WIDTH, SOUND_TRIGGER_ZONE), 0)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        # scroller_y += ((mouse_y- WINDOW_HEIGHT/2)/WINDOW_HEIGHT/2)*50
        speed = WINDOW_HEIGHT * (mouse_y / WINDOW_HEIGHT) * 1.01
        # speed = WINDOW_HEIGHT*(0.2)*1.01
        scroller_y += speed

        BPM = (speed / WINDOW_HEIGHT) * FPS * 60

        if scroller_y > WINDOW_HEIGHT * TOTAL_FRAMES:
            scroller_y = 0
        elif scroller_y < 0:
            scroller_y = WINDOW_HEIGHT * TOTAL_FRAMES

        pygame.draw.line(screen, COLOR_WHITE,
                         (0, WINDOW_HEIGHT - SOUND_TRIGGER_ZONE),
                         (WINDOW_WIDTH, WINDOW_HEIGHT - SOUND_TRIGGER_ZONE), 2)

        FONT_LOG.render_to(screen, (10, 10), f"BPM:{int(BPM)}", COLOR_WHITE)
        FONT_LOG.render_to(screen, (10, 30),
                           f"FPS:{int(pygame_clock.get_fps())}", COLOR_WHITE)
        pygame.display.flip()
        # --- Limit to 60 frames per second
        pygame_clock.tick(FPS)
        if OPTIONS_SAVEFRAMES:
            frame_counter += 1
            pygame.image.save(
                screen,
                f"pygame_record/frame{str(frame_counter).zfill(5)}.png")

    # Close the window and quit.
    pygame.quit()


# /////////////////////////////////////////////

# ----------------------------------------------------------
# ------------------------- MAIN ---------------------------
# ----------------------------------------------------------
if __name__ == "__main__":
    try:
        midifile_name = sys.argv[1]
    except:
        midifile_name = "output.mid"
    start(midifile_name)
