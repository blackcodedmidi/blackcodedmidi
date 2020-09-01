from extract_frames_from_video import extract_frames_from_video
from generate_midifile_from_frames import generate_midifile_from_frames
import midimovies_player


if __name__ == "__main__":
    # extract_frames_from_video("boop.mp4")
    nancarrow_mode_enabled = False    
    generate_midifile_from_frames("boop_color", nancarrow=nancarrow_mode_enabled, clone_multiplier=1)
    midimovies_player.start("output.mid", nancarrow=nancarrow_mode_enabled)