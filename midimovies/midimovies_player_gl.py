# test.py
import moderngl
import moderngl_window as mglw
import numpy as np
import time
import math
import mido

WINDOW_SIZE = (878, 600)

OPTIONS_SENDMIDI = True
_midiport_ = None

BEATS_PER_FRAME = 1
TOTAL_NOTES = 127
NUMBER_OF_CHANNELS = 16
BLACKS_PATTERN = [False, True, False, True, False, False, True, False, True, False, True, False]


song = []
song_length = 0

channels_notes_isplaying = []
for i in range(NUMBER_OF_CHANNELS):
    temp_notes_state = []
    for n in range(TOTAL_NOTES):
        temp_notes_state.append(False)
    channels_notes_isplaying.append(temp_notes_state)


COLOR_BLACK = (0, 0, 0)
COLOR_RED = (1, 0, 0)
COLOR_GREEN = (0, 1, 0)
COLOR_BLUE = (0, 0, 1)
COLOR_YELLOW = (1, 1, 0)
COLOR_WHITE = (1, 1, 1)
COLOR_HOLE = (0, 0, 0)
# paleta arcoiris hipster
COLOR_CHANNELS = [
    [0.01568627450980392,0.32941176470588235,0.34901960784313724],
    [0.03137254901960784,0.45098039215686275,0.3254901960784314],
    [0.08235294117647059,0.7607843137254902,0.5254901960784314],
    [0.6705882352941176,0.8509803921568627,0.42745098039215684],
    [0.984313725490196,0.7490196078431373,0.32941176470588235],
    [0.9333333333333333,0.4196078431372549,0.23137254901960785],
    [0.9254901960784314,0.058823529411764705,0.2784313725490196],
    [0.6274509803921569,0.17254901960784313,0.36470588235294116],
    [0.4392156862745098,0.01568627450980392,0.3764705882352941],
    [0.00784313725490196,0.17254901960784313,0.47843137254901963],
    [0.14901960784313725,0.1607843137254902,0.28627450980392155],
]
# le queda cheto a betty boop
# COLOR_CHANNELS = [
#     (62, 14, 69),
#     (76, 94, 176),
#     (126, 169, 141),
#     (172, 215, 153),
#     (218, 237, 210),
#     (255, 255, 255),
# ]


# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
def loopy_index(array, index):
    length = len(array)

    if index >= length:
        index = index - length
    elif index < 0:
        index = length - index

    index = index % length
    return array[index]
# -----------------------------------------------------------------
def rect(x, y, w, h):
    # mapping to a space from -1 to 1
    x = (x/WINDOW_SIZE[0] - 0.5)*2
    y = (y/WINDOW_SIZE[1] - 0.5)*2
    w = w/WINDOW_SIZE[0] * 2
    h = h/WINDOW_SIZE[1] * 2

    return [x, y,    x+w, y,  x, y+h,
            x, y+h,  x+w, y,  x+w, y+h]
# -----------------------------------------------------------------
class Player(mglw.WindowConfig):
    gl_version = (3, 3)    
    title = "Blackola-GL"
    window_size = WINDOW_SIZE
    aspect_ratio = WINDOW_SIZE[0]/WINDOW_SIZE[1]
    scroller_y = 0
    speed = 0

    def mouse_position_event(self, x, y, dx, dy):
        self.speed = WINDOW_SIZE[1]*(y/WINDOW_SIZE[1])*1.01    

    def render(self, time, frametime):

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec2 in_vert;
                in vec3 in_color;

                out vec3 v_color;

                void main() {
                    v_color = in_color;
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330

                in vec3 v_color;
                out vec3 f_color;

                void main() {
                    f_color = v_color;
                }
            ''',
        )

        vertices = np.array([
            # x, y
            # self.x, 0,
            # -1, -1,
            # 1, -1,
        ])

        colors = np.array([
            # red, green, blue
            # 1.0, 0.0, 0.0,
            # 0.0, 1.0, 1.0,
            # 0.0, 0.0, 1.0,
        ])

        MIDINOTE_OFFSET = 20
        BARGFX_WIDTH = 9
        BARGFX_MARGIN = 1
        WINDOW_HEIGHT = WINDOW_SIZE[1]
        SOUND_TRIGGER_ZONE = int(WINDOW_SIZE[1] / 10)
        FRAMEHEIGHT_AS_SECONDS = BEATS_PER_FRAME / (120 / 60)  # default for created midis is 120 BPM    
        
        TOTAL_FRAMES = math.ceil(song_length / FRAMEHEIGHT_AS_SECONDS)
        
        

        self.scroller_y -= self.speed
        if self.scroller_y > WINDOW_HEIGHT*TOTAL_FRAMES:
            self.scroller_y = 0
        elif self.scroller_y < 0:
            self.scroller_y = WINDOW_HEIGHT*TOTAL_FRAMES


        # grab in wich "frame" of the movie whe are TODO: is this correct? Also, the last frame don't show
        position_in_frames = int(self.scroller_y/WINDOW_HEIGHT)
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
            if (start > self.scroller_y and start < self.scroller_y+WINDOW_HEIGHT) or (end > self.scroller_y and end < self.scroller_y+WINDOW_HEIGHT):
                # print(f"{x} {end - start}")
                # pygame.draw.rect(screen, COLOR_WHITE, (x, start, x+BARGFX_WIDTH, end), 0)
                x = int(x)
                y = WINDOW_HEIGHT - int(end - self.scroller_y)
                w = int(BARGFX_WIDTH)
                h = int(end-start)
                
                for i in range(6):
                    colors = np.append(colors, COLOR_CHANNELS[note[0]])
                vertices = np.append(vertices, rect(x, y, w, h))

            #----- SEND MIDI            
            # TODO: this could be clearer.
            # Main idea is that note[4] is True is the note has already started playing
            # and note[5] is True is the note has already trigger its end state
            # This was for something like stoping the sound to trigger itself multiple times, or something like that.
            if note[4] == False:
                if start < self.scroller_y+SOUND_TRIGGER_ZONE:
                    note[4] = True
                    channels_notes_isplaying[note[0]][note[1]] = True # I think this is used only for the drawing of the piano keys at bottom
                    if OPTIONS_SENDMIDI:
                        msg = mido.Message("note_on", channel=note[0], note=note[1])
                        _midiport_.send(msg)
            elif note[5] == False:
                if end < self.scroller_y+SOUND_TRIGGER_ZONE:
                    note[5] = True
                    channels_notes_isplaying[note[0]][note[1]] = False
                    if OPTIONS_SENDMIDI:
                        msg = mido.Message("note_off", channel=note[0], note=note[1])
                        _midiport_.send(msg)                    
            elif start > self.scroller_y+SOUND_TRIGGER_ZONE and end > self.scroller_y+SOUND_TRIGGER_ZONE:
                # This resets the triggering ability of the notes, when the pianoroll loops, and the movie start again
                note[4] = False
                note[5] = False

        for piano_key in range(127):
            color = None

            #--- paint keys of sounding channel. buggy af
            # for channel_index in range(NUMBER_OF_CHANNELS):
            #     current_channel = channels_notes_isplaying[channel_index]
            #     if current_channel[piano_key] == True:
            #         color = COLOR_CHANNELS[channel_index]

            if not color:
                if BLACKS_PATTERN[piano_key%12]:
                    color = [0, 0, 0]
                else:
                    color = [255, 255, 255]

            for i in range(6):
                colors = np.append(colors, color)
            vertices = np.append(vertices, rect(
                int((piano_key-MIDINOTE_OFFSET)*(BARGFX_WIDTH + BARGFX_MARGIN)),
                int(0),
                BARGFX_WIDTH,
                SOUND_TRIGGER_ZONE))

        self.vbo1 = self.ctx.buffer(vertices.astype('f4').tobytes())
        self.vbo2 = self.ctx.buffer(colors.astype('f4').tobytes())

        self.ctx.clear(0.0, 0.0, 0.0, 0.0)


        self.vao = self.ctx.vertex_array(self.prog, [
            self.vbo1.bind('in_vert', layout='2f'),
            self.vbo2.bind('in_color', layout='3f'),
        ])

        self.vao.render(mode=moderngl.TRIANGLES)
# -----------------------------------------------------------------
def loadmidi(midifile):
    global song
    global song_length
    # --------------------------------------------------------
    # -----------  OPEN MIDI FILE AND PROCESS IT --------
    # ---------------------------------------------------------
    # open midifile and start to format to handy lists
    mid = mido.MidiFile(midifile)
    song_length = mid.length
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
def openMidiPort(output_device=""):
    global _midiport_
    # Open the first output, by default
    if output_device == "":
        outputs = mido.get_output_names()
        print("Available MIDI outputs:", outputs)
        output_device = outputs[0]

    print("MIDI output:", output_device)
    _midiport_ = mido.open_output(output_device)
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
                        default="saved_midis/formula-galaxian.mid",
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
                        default='',
                        help='MIDI output device')

    args = parser.parse_args()

    loadmidi(args.midifile)
    openMidiPort(args.output_device)
    mglw.run_window_config(Player)

if __name__ == "__main__":
    main()