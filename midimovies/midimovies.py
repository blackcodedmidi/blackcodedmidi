import midimovies_player
from extract_frames_from_video import extract_frames_from_video
from generate_midifile_from_frames import generate_midifile_from_frames

if __name__ == "__main__":
    # extract_frames_from_video("boop.mp4")
    # generate_midifile_from_frames("n64")
    midimovies_player.start()
