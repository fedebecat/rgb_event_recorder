import sys
print(sys.path)
# Add /usr/lib/python3/dist-packages/ to PYTHONPATH if the output of print(sys.path) does not mention it.
sys.path.append("/usr/lib/python3/dist-packages/")

from metavision_core.event_io import EventsIterator, LiveReplayEventsIterator, is_live_camera
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette, BaseFrameGenerationAlgorithm
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
import argparse
import os
import cv2
import time
from TemporalBinaryRepresentation import TemporalBinaryRepresentation as TBR
import numpy as np


# def parse_args():
#     """Parse command line arguments."""
#     parser = argparse.ArgumentParser(description='Metavision Simple Viewer sample.',
#                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#     parser.add_argument(
#         '-i', '--input-raw-file', dest='input_path', default="",
#         help="Path to input RAW file. If not specified, the live stream of the first available camera is used. "
#         "If it's a camera serial number, it will try to open that camera instead.")
#     args = parser.parse_args()
#     return args

# The recordings folder contains an event.raw file with the event camera data and a
# "frames" folder containign rgb frames recorded at 30 FPS.
# This script reads both the event stream and the RGB frames and displays them
# in a synchronized manner using opencv.

def main():
    print('start')
    recordings_folder = 'recordings/recording_230920_180138/'
    
    # Read RGB frames and extract timestamps from filenames to check the framerate is ok
    rgb_frames = []
    for filename in os.listdir(recordings_folder + '/frames'):
        if filename.endswith(".jpg"):
            rgb_frames.append({'frame': cv2.imread(os.path.join(recordings_folder + '/frames', filename)),
                               'timestamp': float(filename.split('_')[2].replace('.jpg',''))})
    rgb_frames.sort(key=lambda x: x['timestamp'])
    print(f"len(rgb_frames): {len(rgb_frames)}")
    timestamps = [x['timestamp'] for x in rgb_frames]
    print(timestamps)
    normalized_timestamps = [x - timestamps[0] for x in timestamps]
    diff_timestamps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    # mean diff
    print('checking rgb framerate...')
    print(f"mean diff: {sum(diff_timestamps)/len(diff_timestamps)}")
    print(f'FPS: {1/(sum(diff_timestamps)/len(diff_timestamps))}')

    # Read event stream
    evt_delta_t = 10000
    print('reading event stream...')
    print(f'evt_delta_t: {evt_delta_t}')
    mv_it = EventsIterator(recordings_folder + '/event.raw', delta_t=evt_delta_t)
    print(mv_it)  # show some metadata
    ev_height, ev_width = mv_it.get_size()
    print("\nImager size : ", ev_height, ev_width)

    frame = np.zeros((ev_height, ev_width, 3), dtype=np.uint8)

    # Display synchronized event and rgb frames
    rgb_index = 0
    cv2.imshow("RGB Frame", rgb_frames[0]['frame'])
    key = cv2.waitKey(1) & 0xFF

    for ev in mv_it:
        print(ev.size)
        BaseFrameGenerationAlgorithm.generate_frame(ev, frame) # colors: No event (B:52, G:37, R:30); (200, 126, 64); (255, 255, 255)

        # display image
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        # display rgb synchronized with event timestamp
        evt_timestamp = mv_it.get_current_time()
        evt_timestamp_seconds = evt_timestamp / 1000000
        print(normalized_timestamps[rgb_index], evt_timestamp_seconds)
        if normalized_timestamps[rgb_index] > evt_timestamp_seconds:
            pass
        else:
            print('incrementing rgb index')
            rgb_index += 1
            if rgb_index > len(rgb_frames)-1:
                print('RGB stream finished')
            else:
                # display rgb frame
                cv2.imshow("RGB Frame", rgb_frames[rgb_index]['frame'])
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

