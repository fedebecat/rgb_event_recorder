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
from camera_record import record_video
from multiprocessing import Process, Event
from camera_record import record_video_till_stop
import cv2

'''
This file contains a collection of functions to be used in the main script for recording.
'''

class Recorder:

    def __init__(self, output_dir):
        self.output_dir = output_dir
        # Thread events
        self.thread_event = Event() # thread event for stopping RGB camera
        self.event_camera_event = Event() # thread event for Event camera

        # Output folder
        self.recording_name = "recording_" + time.strftime("%y%m%d_%H%M%S", time.localtime())
        self.log_folder = os.path.join(output_dir, self.recording_name)
        os.makedirs(self.log_folder, exist_ok=True)
        os.makedirs(self.log_folder + '/frames', exist_ok=True)

        # RGB camera thread
        self.cam_record = Process(target=record_video_till_stop, args=(self.thread_event,
                                                                       self.event_camera_event,
                                                                       self.log_folder))
        # Init event camera
        self.device = initiate_device("")
        self.event_log_path = self.log_folder + "/event.raw"
        self.evt_start_timestamp = None

        # Event camera thread
        self.event_record = Process(target=self.record_event)

    def record_event(self):
        # Start the recording with the event camera
        if self.device.get_i_events_stream():
            print(self.event_log_path )
            print(f'Recording event data to {self.event_log_path}')
            self.device.get_i_events_stream().log_raw_data(self.event_log_path)
            print('recording started')
        else:
            print("No event camera found.")

        # Events iterator on Device
        mv_iterator = EventsIterator.from_device(device=self.device)
        height, width = mv_iterator.get_size()  # Camera Geometry
        print(f"Event camera - height: {height}, width: {width}")

        # Process events
        evt_start_timestamp = None
        for evs in mv_iterator:
            if not evt_start_timestamp:
                # As soon as the event camera starts recording, send a trigger to the
                # rgb thread to throw away previously stored frames.
                self.event_camera_event.set()
                evt_start_timestamp = time.time()
                print(f"evt_start_timestamp: {evt_start_timestamp}")

            print(self.thread_event.is_set())
            if self.thread_event.is_set():
                print('stopping event camera')
                # Stop the recording
                self.device.get_i_events_stream().stop_log_raw_data()
                print('done')
                break

    def start_recording_rgb_and_event(self):
        self.cam_record.start()
        self.event_record.start()

    def stop_recording_rgb_and_event(self):
        self.thread_event.set()
        self.cam_record.join()
        self.cam_record.close()


rec = Recorder('recordings')
rec.start_recording_rgb_and_event()

# wait 5 seconds
start_time = time.time()

while time.time() - start_time < 5:
    #print('waiting...')
    pass
print('done waiting')

rec.stop_recording_rgb_and_event()