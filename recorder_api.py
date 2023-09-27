import sys
print(sys.path)
# Add /usr/lib/python3/dist-packages/ to PYTHONPATH if the output of print(sys.path) does not mention it.
sys.path.append("/usr/lib/python3/dist-packages/")

from metavision_core.event_io.raw_reader import initiate_device
from metavision_core.event_io import EventsIterator
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
import time
import os
from multiprocessing import Process, Event
# from camera_record import record_video_till_stop
import cv2
from datetime import datetime, timedelta

'''
This file contains a collection of functions to be used in the main script for recording.
'''


class Recorder:

    def __init__(self):

        # Output folder creation
        self.set_directory()

        # Thread events
        self.stop_recording_trigger = Event() # thread event for stopping RGB camera
        self.ev_start_trigger = Event() # thread event for Event camera
        self.event_camera_has_stopped_trigger = Event()
        self.exit_trigger = Event()

        # Init event camera
        self.device = initiate_device("")
        self.evt_start_timestamp = None

        # # Event camera thread
        # self.event_record = Process(target=self.record_event)

    def record_event(self):
        # Start the recording with the event camera
        if self.device.get_i_events_stream():
            print(self.event_log_path)
            print(f'Recording event data to {self.event_log_path}')
            self.device.get_i_events_stream().log_raw_data(self.event_log_path)
            print('recording started')
        else:
            print("No event camera found.")

        # Events iterator on Device
        mv_iterator = EventsIterator.from_device(device=self.device)
        height, width = mv_iterator.get_size()  # Camera Geometry
        print(f"Event camera - height: {height}, width: {width}")

        close_time = None

        # Process events
        evt_start_timestamp = None
        for evs in mv_iterator:
            if not evt_start_timestamp:
                # As soon as the event camera starts recording, send a trigger to the
                # rgb thread to throw away previously stored frames.
                evt_start_timestamp = time.time()
                print(f"evt_start_timestamp: {evt_start_timestamp}")

            if self.stop_recording_trigger.is_set():
                if close_time is None:
                    close_time = self.get_closing_time()
                    print(f'stopping event camera at {close_time}...')

                # Stop the recording
                if datetime.now() > close_time:
                    self.device.get_i_events_stream().stop_log_raw_data()
                    self.event_camera_has_stopped_trigger.set()
                    print('done')
                    break

    def set_directory(self):
        self.output_dir = 'recordings'
        self.recording_name = "recording_" + datetime.now().strftime('%H:%M:%S.%f')
        self.log_folder = os.path.join(self.output_dir, self.recording_name)
        os.makedirs(self.log_folder, exist_ok=True)
        os.makedirs(self.log_folder + '/frames', exist_ok=True)
        self.event_log_path = self.log_folder + "/event.raw"
        print(f"Recording to {self.log_folder}")
    
    def record_rgb_synch(self):
        #start video capture
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # set framerate
        FPS = 30.0
        cap.set(cv2.CAP_PROP_FPS, FPS)
        freq_frames = 1/FPS
        frame_buffer = []

        # be sure that the internal camera buffer is empty
        for _ in range(5):
            cap.grab()

        close_timestamp = None
        is_recording = False

        # grab frames continously but store in buffer only at the desired frequency
        while True:
            grabbed = cap.grab()

            if self.ev_start_trigger.is_set() and not is_recording:
                print('#################### starting rgb camera...')
                print('starting rgb camera...')
                is_recording = True
                # store first frame
                _, frame = cap.retrieve()
                start_timestamp = datetime.now()
                last_frame_timestamp = start_timestamp
                frame_buffer.append({'frame': frame, 'timestamp': last_frame_timestamp})

            if is_recording:
                # store frame at desired frequency
                if (datetime.now() - last_frame_timestamp).total_seconds() > freq_frames:
                    _, frame = cap.retrieve()
                    last_frame_timestamp = datetime.now()
                    frame_buffer.append({'frame': frame, 'timestamp': last_frame_timestamp})
            
                if self.stop_recording_trigger.is_set() and is_recording:
                    if close_timestamp is None:
                        close_timestamp = self.get_closing_time()
                        print(f'stopping rgb camera at {close_timestamp}...')
                    if datetime.now() > close_timestamp:
                        is_recording = False

                        duration = close_timestamp - start_timestamp
                        print(f"duration: {duration.total_seconds()}")
                        fps = len(frame_buffer)/(duration.total_seconds())
                        print(f"frames: {len(frame_buffer)}")
                        print(f"actual fps: {fps} ---- desired fps: {FPS}")
                        print(f"len(frame_buffer): {len(frame_buffer)}")
                        print(f"duration: {duration}")

                        print("saving video frames")
                        # The loop goes through the array of images and writes each image to the video file
                        for i in range(len(frame_buffer)):
                            # save video as frames in the frames folder. Add timestamp to filename
                            cur_timestamp = frame_buffer[i]['timestamp']
                            if cur_timestamp <= close_timestamp:
                                cv2.imwrite(f"{self.log_folder}/frames/frame_{i}_{cur_timestamp.strftime('%H:%M:%S.%f')}.jpg",
                                            frame_buffer[i]['frame'])
            
                        frame_buffer = []
                        close_timestamp = None
                        print("Done")
            if self.exit_trigger.is_set():
                print('Exiting camera thread...')
                break

    def start_recording_rgb_and_event(self):
        self.exit_trigger.clear()
        self.stop_recording_trigger.clear()
        # RGB camera thread
        self.cam_record = Process(target=self.record_rgb_synch, args=())
        self.cam_record.start()

        time.sleep(2)

        # Event camera thread
        self.event_record = Process(target=self.record_event)
        self.ev_start_trigger.set()
        self.event_record.start()

    def stop_recording_rgb_and_event(self):
        close_time = datetime.now() + timedelta(seconds=1)
        close_time -= timedelta(microseconds=close_time.microsecond)
        print(f"close_time: {close_time}")
        self.stop_recording_trigger.set()
        # reset trigger
        self.ev_start_trigger.clear()
        self.event_record.join()
        self.event_record.close()
        self.exit()

    def get_closing_time(self):
        close_time = datetime.now() + timedelta(seconds=1)
        close_time -= timedelta(microseconds=close_time.microsecond)
        print(f"close_time: {close_time.strftime('%H:%M:%S.%f')}")
        return close_time
    
    def exit(self):
        self.exit_trigger.set()
        self.cam_record.join()
        self.cam_record.close()


def sanity_check(recordings_folder):
    # TODO: not working yet
    # Read RGB frames and extract timestamps from filenames to check the framerate is ok
    rgb_frames = []
    for filename in os.listdir(recordings_folder + '/frames'):
        if filename.endswith(".jpg"):
            rgb_frames.append({'frame': cv2.imread(os.path.join(recordings_folder + '/frames', filename)),
                               'timestamp': filename.split('_')[2].replace('.jpg','')})
    rgb_frames.sort(key=lambda x: x['timestamp'])
    print(f"len(rgb_frames): {len(rgb_frames)}")
    timestamps = [x['timestamp'] for x in rgb_frames]
    # convert timestaps to datetime objects parsing strings like 09:40:48.042800
    timestamps = [datetime.strptime(str(x), '%H:%M:%S.%f') for x in timestamps]

    print(timestamps)
    normalized_timestamps = [x - timestamps[0] for x in timestamps]
    diff_timestamps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    # mean diff
    print('checking rgb framerate...')
    print(f"mean diff: {sum(diff_timestamps)/len(diff_timestamps)}")
    print(f'FPS: {1/(sum(diff_timestamps)/len(diff_timestamps))}')
    print(f'duration: {timestamps[-1] - timestamps[0]}')



rec = Recorder()

time.sleep(3)

rec.start_recording_rgb_and_event()

# wait 5 seconds
start_time = time.time()

while time.time() - start_time < 4:
    #print('waiting...')
    pass
print('done waiting')

rec.stop_recording_rgb_and_event()

print('-----------------------FIRST RECORDING DONE-----------------------')

time.sleep(5)

rec.set_directory()
rec.start_recording_rgb_and_event()
# wait 5 seconds
start_time = time.time()

while time.time() - start_time < 4:
    #print('waiting...')
    pass
print('done waiting')

rec.stop_recording_rgb_and_event()

print('-----------------------SECOND RECORDING DONE-----------------------')