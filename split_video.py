import os.path
import numpy as np

import moviepy.utils
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


def split_via_size(movie):
    cuts = []
    s = os.path.getsize(movie)
    duration = VideoFileClip(movie).duration
    split_time = int(s / 1_450_000_000)

    if split_time != 0:
        duration_part = duration / (split_time + 1)
        for i in np.arange(0.0, duration, duration_part):
            cut_name = 'cut{}.mp4'.format(int(i))
            cuts.append(cut_name)
            ffmpeg_extract_subclip(movie, i, i + duration_part, targetname=cut_name)

    os.system("taskkill /im ffmpeg-win64-v4.2.2.exe /t /f")
    moviepy.utils.close_all_clips()
    return cuts
