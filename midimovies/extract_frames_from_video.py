import subprocess
import shutil
import os
from PIL import Image, ImageOps
import sys

# ------------------------------------------------------------------------
# ------------------------- EXTRACT FRAMES FROM VIDEO --------------------
# ------------------------------------------------------------------------
def extract_frames_from_video(videoname):
    PATH_TEMP_FRAMES = os.getcwd() + "/temp/"
    PATH_FINAL_FRAMES = os.getcwd() + "/movies_as_frames/frames/"
    OUTPUT_SIZE = (88, 64)
    #-----------
    if not os.path.exists(PATH_FINAL_FRAMES):
        os.mkdir(PATH_FINAL_FRAMES)
    if os.path.exists(PATH_TEMP_FRAMES):
        shutil.rmtree(PATH_TEMP_FRAMES)
    os.mkdir(PATH_TEMP_FRAMES)
    #-----------

    command = "ffmpeg -i {in_name} -r 24/1 {out_name}".format(
        in_name=videoname, out_name=PATH_TEMP_FRAMES + "ffmpeg_%05d.bmp")
    subprocess.call(command, shell=True)
    # --------------------------------------------------
    # postproceses frames, resize and posterize
    for entry in os.listdir(PATH_TEMP_FRAMES):
        img = Image.open(PATH_TEMP_FRAMES + entry)
        img = img.resize(OUTPUT_SIZE, Image.NEAREST)
        img = ImageOps.posterize(img, 2)
        img.save(PATH_FINAL_FRAMES + f"{entry}.png")

    if os.path.exists(PATH_TEMP_FRAMES):
        shutil.rmtree(PATH_TEMP_FRAMES)
# /////////////////////////////////////////////


# ----------------------------------------------------------
# ------------------------- MAIN ---------------------------
# ----------------------------------------------------------
if __name__ == "__main__":
    try:
        videofile_name = sys.argv[1]
    except:
        videofile_name = "video.mp4"
    extract_frames_from_video(videofile_name)
