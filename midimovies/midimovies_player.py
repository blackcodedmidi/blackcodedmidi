#!/usr/bin/env python3
import os
import mido
import mido.backends.rtmidi #explicit import for when building the .exe
import pygame
import pygame.freetype  # Import the freetype module.
import math
import argparse


# ------------------------------------------------------------------------
# ------------------------- PLAYER ---------------------------------------
# ------------------------------------------------------------------------
def start(midifile_name="output.mid", output_device=None):

    BEATS_PER_FRAME = 1

    TOTAL_NOTES = 127


    # Open the first output, by default
    if not output_device:
        outputs = mido.get_output_names()
        print("Outputs:", outputs)
        output_device = outputs[0]

    print("MIDI output:", output_device)
    _midiport_ = mido.open_output(output_device)

    mid = mido.MidiFile(midifile_name)
    song = []

    start_times = [[None] * TOTAL_NOTES, [None] * TOTAL_NOTES, [None] * TOTAL_NOTES, [None] * TOTAL_NOTES, [None] * TOTAL_NOTES]

    timer = 0
    # formatea la data midi a algo con menos cancer. para que cada nota tenga su start y end
    for msg in mid:
        # print(msg)
        if not isinstance(msg, mido.MetaMessage):
            # msg.time come as seconds
            # timer += mido.second2tick(msg.time, mid.ticks_per_beat, 500000)
            timer += msg.time

            # print(timer)
            if(msg.type == "note_on"):
                # print(f"save time on channel {msg.channel}:{msg.note} = {timer}")
                start_times[msg.channel][msg.note] = timer
            elif(msg.type == 'note_off'):
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

    COLOR_CHANNELS = [COLOR_RED, COLOR_GREE, COLOR_BLUE, COLOR_YELLOW]
    # COLOR_CHANNELS = [(50, 50, 50), (100, 100, 100), (150, 150, 150), (200, 200, 200)]

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
    MIDINOTE_OFFSET = 20 #first 20 midinotes are silent


    scroller_y = 0

    #default for created midis is 120 BPM
    FRAMEHEIGHT_AS_SECONDS = BEATS_PER_FRAME / (120/60)
    SOUND_TRIGGER_ZONE = WINDOW_HEIGHT/10
    TOTAL_FRAMES = math.ceil(mid.length / FRAMEHEIGHT_AS_SECONDS)

    TOTAL_CHANNELS = len(COLOR_CHANNELS)

    channels_notes_isplaying = []
    for i in range(TOTAL_CHANNELS):
        temp_notes_state = []
        for n in range(TOTAL_NOTES):
            temp_notes_state.append(False)
        channels_notes_isplaying.append(temp_notes_state)

    BLACKS_PATTERN = [False, True, False, True, False, False, True, False, True, False, True, False]


    while not EXIT:
        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                EXIT = True


        screen.fill(COLOR_BLACK)

        for note in song:

            baddata = False
            for d in note:
                if d is None:
                    baddata = True

            if baddata:
                continue

            x = (note[1]-MIDINOTE_OFFSET)*(BARGFX_WIDTH + BARGFX_MARGIN)
            start = (note[2]/FRAMEHEIGHT_AS_SECONDS) * WINDOW_HEIGHT
            end = (note[3]/FRAMEHEIGHT_AS_SECONDS) * WINDOW_HEIGHT
            # print(f"start {start} / end {end}")

            #draw
            if (start > scroller_y and start < scroller_y+WINDOW_HEIGHT) or (end > scroller_y and end < scroller_y+WINDOW_HEIGHT):
                # print(f"{x} {end - start}")
                # pygame.draw.rect(screen, COLOR_WHITE, (x, start, x+BARGFX_WIDTH, end), 0)
                x = int(x)
                y = int(WINDOW_HEIGHT - (end - scroller_y))
                w = int(BARGFX_WIDTH)
                h = int((end-start))
                pygame.draw.rect(screen, COLOR_CHANNELS[note[0]], (x, y, w, h), 0)

            # sound
            if True:
                if note[4] == False:
                    if start < scroller_y+SOUND_TRIGGER_ZONE:
                        note[4] = True
                        channels_notes_isplaying[note[0]][note[1]] = True
                        msg = mido.Message("note_on", channel=note[0], note=note[1])
                        _midiport_.send(msg)
                elif note[5] == False:
                    if end < scroller_y+SOUND_TRIGGER_ZONE:
                        note[5] = True
                        channels_notes_isplaying[note[0]][note[1]] = False
                        msg = mido.Message("note_off", channel=note[0], note=note[1])
                        _midiport_.send(msg)
                elif start > scroller_y+SOUND_TRIGGER_ZONE and end > scroller_y+SOUND_TRIGGER_ZONE:
                    note[4] = False
                    note[5] = False

        for piano_key in range(TOTAL_NOTES):
            color = None
            for channel_index in range(TOTAL_CHANNELS):
                current_channel = channels_notes_isplaying[channel_index]
                if current_channel[piano_key] == True:
                    color = COLOR_CHANNELS[channel_index]
            if not color:
                if BLACKS_PATTERN[piano_key%12]:
                    color = COLOR_BLACK
                else:
                    color = COLOR_WHITE
            pygame.draw.rect(screen, color, ((piano_key-MIDINOTE_OFFSET)*(BARGFX_WIDTH + BARGFX_MARGIN), WINDOW_HEIGHT-SOUND_TRIGGER_ZONE, BARGFX_WIDTH, SOUND_TRIGGER_ZONE), 0)


        mouse_x, mouse_y = pygame.mouse.get_pos()
        # scroller_y += ((mouse_y- WINDOW_HEIGHT/2)/WINDOW_HEIGHT/2)*50
        speed = WINDOW_HEIGHT*(mouse_y/WINDOW_HEIGHT)*1.01
        # speed = WINDOW_HEIGHT*(0.2)*1.01
        scroller_y += speed

        BPM = (speed/WINDOW_HEIGHT)*FPS*60

        if scroller_y > WINDOW_HEIGHT*TOTAL_FRAMES:
            scroller_y = 0
        elif scroller_y < 0:
            scroller_y = WINDOW_HEIGHT*TOTAL_FRAMES


        pygame.draw.line(screen, COLOR_WHITE, (0, WINDOW_HEIGHT-SOUND_TRIGGER_ZONE), (WINDOW_WIDTH, WINDOW_HEIGHT-SOUND_TRIGGER_ZONE), 2)

        FONT_LOG.render_to(screen, (10, 10), f"BPM:{int(BPM)}", COLOR_WHITE)
        FONT_LOG.render_to(screen, (10, 30), f"FPS:{int(pygame_clock.get_fps())}", COLOR_WHITE)
        pygame.display.flip()
        # --- Limit to 60 frames per second
        pygame_clock.tick(FPS)

    # Close the window and quit.
    pygame.quit()
# /////////////////////////////////////////////


# ----------------------------------------------------------
# ------------------------- MAIN ---------------------------
# ----------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Plays a MIDI file.')
    parser.add_argument('input', help='a MIDI file')
    parser.add_argument('--output-device', '-o', default=None,
                        help='MIDI output device (default: use the first one)')

    args = parser.parse_args()
    start(args.input, output_device=args.output_device)


if __name__ == "__main__":
    main()
