import ast  # transform arrays formated string to real arrays
import math
import sys
import threading
import time
import os

import mido
import moderngl
import moderngl_window as mglw
import numpy as np
# osc stuff
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer


# -----------------------------------------------------------------
# -----------------------------------------------------------------


WINDOW_SIZE = (878, 600)
mouse_pos = WINDOW_SIZE

LOOP_GLUE = True

OPTIONS_SENDMIDI = True
_midiport_ = None
master_volume = 1.0

# well not really seconds, but if a note is the size of the height of the window, the start is 0 and the end is 1
# is seconds is the movie2frame is set at 60bpm
FRAMEHEIGHT_AS_SECONDS = 1
player_speed = 0.2
player_targetspeed = player_speed
player_targetspeed_step = 0
player_speed_tweening = False
# from 0 to 100 for a whole window height in each step

TOTAL_FRAMES = None
TOTAL_NOTES = 127
NUMBER_OF_CHANNELS = 16
BLACKS_PATTERN = [
    False, True, False, True, False, False, True, False, True, False, True,
    False
]

song = []
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
# COLOR_CHANNELS = [
#     [0.01568627450980392, 0.32941176470588235, 0.34901960784313724],
#     [0.03137254901960784, 0.45098039215686275, 0.3254901960784314],
#     [0.08235294117647059, 0.7607843137254902, 0.5254901960784314],
#     [0.6705882352941176, 0.8509803921568627, 0.42745098039215684],
#     [0.984313725490196, 0.7490196078431373, 0.32941176470588235],
#     [0.9333333333333333, 0.4196078431372549, 0.23137254901960785],
#     [0.9254901960784314, 0.058823529411764705, 0.2784313725490196],
#     [0.6274509803921569, 0.17254901960784313, 0.36470588235294116],
#     [0.4392156862745098, 0.01568627450980392, 0.3764705882352941],
#     [0.00784313725490196, 0.17254901960784313, 0.47843137254901963],
#     [0.14901960784313725, 0.1607843137254902, 0.28627450980392155],
# ]

COLOR_CHANNELS = [COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_WHITE]
# le queda cheto a betty boop
# COLOR_CHANNELS = [
#     (62, 14, 69),
#     (76, 94, 176),
#     (126, 169, 141),
#     (172, 215, 153),
#     (218, 237, 210),
#     (255, 255, 255),
# ]

# --
# GL


def run_window_config(config_cls: mglw.WindowConfig,
                      timer=None,
                      args=None) -> None:
    """
    Run an WindowConfig entering a blocking main loop

    Args:
        config_cls: The WindowConfig class to render
        args: Override sys.args
    """
    mglw.setup_basic_logging(config_cls.log_level)
    parser = mglw.create_parser()
    config_cls.add_arguments(parser)
    values = parse_args(args=args, parser=parser)
    config_cls.argv = values
    window_cls = mglw.get_local_window_cls(values.window)

    # Calculate window size
    size = values.size or config_cls.window_size
    size = int(size[0] * values.size_mult), int(size[1] * values.size_mult)

    # Resolve cursor
    show_cursor = values.cursor
    if show_cursor is None:
        show_cursor = config_cls.cursor

    window = window_cls(
        title=config_cls.title,
        size=size,
        fullscreen=config_cls.fullscreen or values.fullscreen,
        resizable=values.resizable
        if values.resizable is not None else config_cls.resizable,
        gl_version=config_cls.gl_version,
        aspect_ratio=config_cls.aspect_ratio,
        vsync=values.vsync if values.vsync is not None else config_cls.vsync,
        samples=values.samples
        if values.samples is not None else config_cls.samples,
        cursor=show_cursor if show_cursor is not None else True,
    )
    window.print_context_info()
    mglw.activate_context(window=window)
    timer = mglw.Timer()
    window.config = config_cls(ctx=window.ctx, wnd=window, timer=timer)

    timer.start()

    while not window.is_closing:
        current_time, delta = timer.next_frame()

        if window.config.clear_color is not None:
            window.clear(*window.config.clear_color)
        else:
            window.use()
        window.render(current_time, delta)
        if not window.is_closing:
            window.swap_buffers()

    _, duration = timer.stop()
    window.destroy()
    if duration > 0:
        mglw.logger.info("Duration: {0:.2f}s @ {1:.2f} FPS".format(
            duration, window.frames / duration))


def parse_args(args=None, parser=None):
    """Parse arguments from sys.argv

    Passing in your own argparser can be user to extend the parser.

    Keyword Args:
        args: override for sys.argv
        parser: Supply your own argparser instance
    """
    parser = parser or mglw.create_parser()
    return parser.parse_args(args if args is not None else sys.argv[1:])


# -----------------------------------------------------------------
# -----------------------------------------------------------------
# OSC stuff
def refreshSong(address, *args):
    global song
    global TOTAL_FRAMES

    filename = f"{args[0]}.txt"
    f = open(os.path.join(os.path.dirname(__file__), "songs",filename), "r")
    song = f.read()
    f.close()

    song = ast.literal_eval(song)

    TOTAL_FRAMES = len(song)
    if LOOP_GLUE:
        song = duplicateFirstFrameAtTheEnd(song)

    print(f"refresh: {filename}")


def setTagetSpeed(address, *args):
    global player_speed
    global player_speed_tweening
    global player_targetspeed
    global player_targetspeed_tweentime
    global player_targetspeed_step
    
    if len(args) > 1:        
        player_targetspeed = args[0]
        player_targetspeed_tweentime = args[1]
        if player_targetspeed_tweentime in [0, None]:
            player_speed = args[0]
            player_speed_tweening = False
        else:
            player_targetspeed_step = abs(player_speed - player_targetspeed)/player_targetspeed_tweentime;
            player_targetspeed_step *= 1 if (player_targetspeed - player_speed > 0) else -1
            player_speed_tweening = True
    else:
        player_speed = args[0]
        player_speed_tweening = False

def setMasterVolume(address, *args):
    global master_volume
    master_volume = np.clip(float(args[0]),0,1)


def tweenSpeed(frametime):
    global player_speed
    global player_speed_tweening
    global player_targetspeed
    global player_targetspeed_step

    player_speed += player_targetspeed_step*frametime

    reached_target = False
    if player_targetspeed_step > 0:
        if player_speed > player_targetspeed:
            reached_target = True
    elif player_speed < player_targetspeed:
            reached_target = True

    if reached_target:
        player_speed = player_targetspeed
        player_speed_tweening = False

    return player_speed



def startServer():
    dispatcher = Dispatcher()
    dispatcher.map("/refresh", refreshSong)
    dispatcher.map("/speed", setTagetSpeed)
    dispatcher.map("/master", setMasterVolume)    
    ip = "127.0.0.1"
    port = 1337
    server = BlockingOSCUDPServer((ip, port), dispatcher)
    server.serve_forever()  # Blocks forever


# -----------------------------------------------------------------
# -----------------------------------------------------------------
def duplicateFirstFrameAtTheEnd(song):
    number_of_frames = len(song)

    cloned_first_frame = []

    for note in song[0]:  # for notes in first frame
        new_note = note.copy()
        new_note[0] = number_of_frames
        cloned_first_frame.append(new_note)
    song.append(cloned_first_frame)
    return song


# -----------------------------------------------------------------
# -----------------------------------------------------------------
# Handy DRAW functions:
# put toghether vertices to create a 'rectangle'
def rect(x, y, w, h):
    # mapping to a space from -1 to 1
    x = (x / WINDOW_SIZE[0] - 0.5) * 2
    y = (y / WINDOW_SIZE[1] - 0.5) * 2
    w = w / WINDOW_SIZE[0] * 2
    h = h / WINDOW_SIZE[1] * 2

    return [x, y, x + w, y, x, y + h, x, y + h, x + w, y, x + w, y + h]


# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
class Player(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Blackola-GL"
    window_size = WINDOW_SIZE
    aspect_ratio = WINDOW_SIZE[0] / WINDOW_SIZE[1]
    scroller_y = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.texture = self.ctx.texture(WINDOW_SIZE, components=4, dtype='f1')
        self.depth_attachment = self.ctx.depth_renderbuffer(WINDOW_SIZE)
        self.offscreen = self.ctx.framebuffer(self.texture,
                                              self.depth_attachment)

        self.currentframe_texture = self.ctx.texture(WINDOW_SIZE,
                                                     components=4,
                                                     dtype='f1')
        self.currentframe_depth_attachment = self.ctx.depth_renderbuffer(
            WINDOW_SIZE)
        self.currentframe = self.ctx.framebuffer(
            self.currentframe_texture, self.currentframe_depth_attachment)

        self.prevframe_texture = self.ctx.texture(WINDOW_SIZE,
                                                  components=4,
                                                  dtype='f1')
        self.prevframe_depth_attachment = self.ctx.depth_renderbuffer(
            WINDOW_SIZE)
        self.prevframe = self.ctx.framebuffer(self.prevframe_texture,
                                              self.prevframe_depth_attachment)

        self.prog_basictriangles = self.ctx.program(
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

        self.program_postprocess = self.ctx.program(
            vertex_shader="""
            #version 330

            in vec2 in_pos;
            in vec2 in_uv;
            out vec2 uv;

            void main() {
                gl_Position = vec4(in_pos, 0.0, 1.0);
                uv = in_uv;
            }
            """,
            fragment_shader="""
            #version 330

            uniform sampler2D texture0;
            uniform sampler2D texture1;
            uniform float time;
            out vec4 fragColor;
            in vec2 uv;

            void main() {
                float pi = 3.14159265359;
                vec2 st = uv;

                st -= 0.5;
                st.x *= 1.05 - sin(uv.y*pi)*0.15;
                st.y *= 1.00 - sin(uv.y*pi)*0.05;
                st += 0.5;

                vec4 currentFrame = texture(texture0, st);
                currentFrame.a = step(0.2, (currentFrame.r+currentFrame.g+currentFrame.b)/3);
                vec4 prevframe = texture(texture1, uv);
                prevframe.a = step(0.2, (prevframe.r+prevframe.g+prevframe.b)/3);
                fragColor = mix(prevframe, currentFrame, 0.99);
                fragColor = currentFrame;
            }
            """,
        )
        screen_quad = self.ctx.buffer(
            np.array([
                # x, y, u, v
                -1,
                1,
                0.0,
                1.0,
                -1,
                -1,
                0.0,
                0.0,
                1,
                1,
                1.0,
                1.0,
                1,
                -1,
                1.0,
                0.0,
            ]).astype('f4').tobytes())
        self.vao_quad = self.ctx.vertex_array(
            self.program_postprocess,
            [(screen_quad, '2f 2f', 'in_pos', 'in_uv')])
        #  MAKES SURE THE UNIFORM IS USED OR GET REMOVED WHEN THE SHADER IS COMPILED
        # self.uniform_time = self.program_postprocess["time"]
        # self.uniform_time.value = 1.0

        self.program_simple = self.ctx.program(
            vertex_shader="""
            #version 330

            in vec2 in_pos;
            in vec2 in_uv;
            out vec2 uv;

            void main() {
                gl_Position = vec4(in_pos, 0.0, 1.0);
                uv = in_uv;
            }
            """,
            fragment_shader="""
            #version 330

            uniform sampler2D texture0;
            out vec4 fragColor;
            in vec2 uv;

            void main() {
                float r = texture(texture0, uv).r;
                float g = texture(texture0, uv-0.001).g;
                float b = texture(texture0, uv+0.001).b;
                float a = texture(texture0, uv).a;
                fragColor = vec4(r,g,b,a);
            }
            """,
        )
        self.vao_simple = self.ctx.vertex_array(
            self.program_simple, [(screen_quad, '2f 2f', 'in_pos', 'in_uv')])

    def mouse_position_event(self, x, y, dx, dy):
        global mouse_pos
        mouse_pos = [x, y]

    def render(self, time, frametime):
        global player_speed
        global player_speed_tweening
        global mouse_pos
        global master_volume

        if (mouse_pos[0] < 80):
            player_speed = (mouse_pos[1] / WINDOW_SIZE[1]) * 100.2
        elif player_speed_tweening:
            player_speed = tweenSpeed(frametime)

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
        SOUND_TRIGGER_ZONE = WINDOW_HEIGHT // 10

        self.scroller_y += (player_speed / 100) * WINDOW_HEIGHT
        if self.scroller_y > WINDOW_HEIGHT * TOTAL_FRAMES:
            self.scroller_y = 0  # before was 0, and the first note doesn't played
        elif self.scroller_y < -SOUND_TRIGGER_ZONE:  #before was 0, and the first note doesn't played
            self.scroller_y = WINDOW_HEIGHT * TOTAL_FRAMES

        # grab in wich "frame" of the movie whe are TODO: is this correct? Also, the last frame don't show
        position_in_frames = int(self.scroller_y / WINDOW_HEIGHT)
        # print(position_in_frames)
        # grabing just the frames that that have a chance of drawing or making sound in this iteration
        notes_to_check = []
        notes_to_check += song[(position_in_frames - 1) % len(song)]
        notes_to_check += song[(position_in_frames) % len(song)]
        notes_to_check += song[(position_in_frames + 1) % len(song)]

        for note in notes_to_check:
            # fail safe check, skip note if it has something weird
            if len(note) != 8:
                print("-- FAIL -- ")
                print(f"note: {note}")
                continue

            # converting note's start and end values to screen's height porcentage
            # [frame_index, channel, note, velocity, start, end, false, false]

            note_key = note[2]
            channel = note[1]
            x = (note[2] - MIDINOTE_OFFSET) * (BARGFX_WIDTH + BARGFX_MARGIN)
            start = note[0] * FRAMEHEIGHT_AS_SECONDS + note[4]
            end = note[0] * FRAMEHEIGHT_AS_SECONDS + note[5]
            start = start * WINDOW_HEIGHT
            end = end * WINDOW_HEIGHT
            velocity = int(note[3] * master_volume)


            #----- DRAW NOTE
            if (start > self.scroller_y
                    and start < self.scroller_y + WINDOW_HEIGHT) or (
                        end > self.scroller_y
                        and end < self.scroller_y + WINDOW_HEIGHT):
                # print(f"{x} {end - start}")
                # pygame.draw.rect(screen, COLOR_WHITE, (x, start, x+BARGFX_WIDTH, end), 0)
                x = int(x)
                y = int(start - self.scroller_y)
                w = int(BARGFX_WIDTH)
                h = int(end - start)

                for i in range(6):
                    colors = np.append(
                        colors, COLOR_CHANNELS[note[1] % len(COLOR_CHANNELS)])
                vertices = np.append(vertices, rect(x, y, w, h))

            #----- SEND MIDI
            # TODO: this could be clearer.
            # Main idea is that note[6] is True is the note has already started playing
            # and note[5] is True is the note has already trigger its end state
            # This was for something like stoping the sound to trigger itself multiple times, or something like that.
            if player_speed >= 0: 
                if note[6] == False:
                    if start < self.scroller_y + SOUND_TRIGGER_ZONE:
                        note[6] = True
                        # I think this is used only for the drawing of the piano keys at bottom
                        channels_notes_isplaying[channel][note_key] = True
                        if OPTIONS_SENDMIDI:
                            msg = mido.Message("note_on",
                                               channel=channel,
                                               note=note_key,
                                               velocity=velocity)
                            _midiport_.send(msg)
                elif note[7] == False:
                    if end < self.scroller_y + SOUND_TRIGGER_ZONE:
                        note[7] = True
                        channels_notes_isplaying[channel][note_key] = False
                        if OPTIONS_SENDMIDI:
                            msg = mido.Message("note_off",
                                               channel=channel,
                                               note=note_key)
                            _midiport_.send(msg)
                elif start > self.scroller_y + SOUND_TRIGGER_ZONE and end > self.scroller_y + SOUND_TRIGGER_ZONE:
                    # This resets the triggering ability of the notes, when the pianoroll loops, and the movie start again
                    note[6] = False
                    note[7] = False
            else:
                if note[7] == False:
                    if end > self.scroller_y + SOUND_TRIGGER_ZONE:
                        note[7] = True
                        # I think this is used only for the drawing of the piano keys at bottom
                        channels_notes_isplaying[channel][note_key] = True
                        if OPTIONS_SENDMIDI:
                            msg = mido.Message("note_on",
                                               channel=channel,
                                               note=note_key,
                                               velocity=velocity)
                            _midiport_.send(msg)
                elif note[6] == False:
                    if start > self.scroller_y + SOUND_TRIGGER_ZONE:
                        note[6] = True
                        channels_notes_isplaying[channel][note_key] = False
                        if OPTIONS_SENDMIDI:
                            msg = mido.Message("note_off",
                                               channel=channel,
                                               note=note_key)
                            _midiport_.send(msg)
                elif start < self.scroller_y + SOUND_TRIGGER_ZONE and end < self.scroller_y + SOUND_TRIGGER_ZONE:
                    # This resets the triggering ability of the notes, when the pianoroll loops, and the movie start again
                    note[6] = False
                    note[7] = False

        for piano_key in range(127):
            color = None

            # paint keys of sounding channel
            for channel_index in range(NUMBER_OF_CHANNELS):
                current_channel = channels_notes_isplaying[channel_index]
                if current_channel[piano_key] == True:
                    color = COLOR_CHANNELS[channel_index % len(COLOR_CHANNELS)]

            if not color:
                if BLACKS_PATTERN[piano_key % 12]:
                    color = [0, 0, 0]
                else:
                    color = [255, 255, 255]

            for i in range(6):
                colors = np.append(colors, color)
            vertices = np.append(
                vertices,
                rect(
                    int((piano_key - MIDINOTE_OFFSET) *
                        (BARGFX_WIDTH + BARGFX_MARGIN)), int(0), BARGFX_WIDTH,
                    SOUND_TRIGGER_ZONE))

        # this appears to need to be updated every frame
        self.vbo1 = self.ctx.buffer(vertices.astype('f4').tobytes())
        self.vbo2 = self.ctx.buffer(colors.astype('f4').tobytes())
        self.vao = self.ctx.vertex_array(self.prog_basictriangles, [
            self.vbo1.bind('in_vert', layout='2f'),
            self.vbo2.bind('in_color', layout='3f'),
        ])

        # -----------------
        # RENDER
        # -----------------
        # Render the triangles to offscreen buffer
        self.offscreen.clear(0.0, 0.0, 0.0, 0.0)
        self.offscreen.use()
        self.ctx.enable_only(moderngl.NOTHING)
        # self.ctx.enable_only(moderngl.DEPTH_TEST)
        self.vao.render(mode=moderngl.TRIANGLES)

        # postprocess triangle texture to currentframebuffer
        self.currentframe.use()
        self.currentframe.clear(0.0, 0.0, 0.0)
        # activate texture from the offscreen buffer
        # self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA
        # self.ctx.enable_only(moderngl.BLEND)
        self.texture.use(0)
        self.prevframe_texture.use(1)
        self.ctx.enable_only(moderngl.BLEND)
        # self.uniform_time.value = time
        self.vao_quad.render(mode=moderngl.TRIANGLE_STRIP)

        # render (TODO: its should just copy it) currentframe_texture to preframe buffer
        self.prevframe.use()
        self.prevframe.clear(0.0, 0.0, 0.0)
        self.currentframe_texture.use(0)
        self.ctx.enable_only(moderngl.BLEND)
        self.vao_simple.render(mode=moderngl.TRIANGLE_STRIP)

        # Activate the window and render currentframe
        self.ctx.screen.use()
        self.ctx.clear(0.0, 0.0, 0.1)
        self.currentframe_texture.use(0)
        self.ctx.enable_only(moderngl.BLEND)
        self.vao_simple.render(mode=moderngl.TRIANGLE_STRIP)


# -----------------------------------------------------------------
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
def start_player(midifile=None, output_device=None, mglw_args=None):
    threading.Thread(target=startServer, daemon=True).start()

    openMidiPort(output_device)

    refreshSong("/refresh", "init")
    run_window_config(Player, args=mglw_args)


if __name__ == "__main__":
    import argparse

    mido.get_output_names()


    parser = argparse.ArgumentParser(
        description="BlackolaGL MIDI player",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m",
                        "--midifile",
                        default="output.mid",
                        help="MIDI file to play")
    parser.add_argument('--output-device',
                        '-o',
                        default='OmniMIDI 1',
                        help='MIDI output device')

    args, extra_args = parser.parse_known_args()

    start_player(midifile=args.midifile,
                 output_device=args.output_device,
                 mglw_args=extra_args)
