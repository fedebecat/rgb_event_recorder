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
from video_capture import VideoCaptureAsyncWithTimestamp
from datetime import datetime, timedelta

'''
This file contains a collection of functions to be used in the main script for recording.
'''


class Recorder:

    def __init__(self, output_dir):
        self.output_dir = output_dir
        # Thread events
        self.thread_event = Event() # thread event for stopping RGB camera
        self.event_camera_event = Event() # thread event for Event camera
        self.event_camera_has_stopped = Event()

        # Output folder
        self.recording_name = "recording_" + datetime.now().strftime('%H:%M:%S.%f')
        self.log_folder = os.path.join(output_dir, self.recording_name)
        os.makedirs(self.log_folder, exist_ok=True)
        os.makedirs(self.log_folder + '/frames', exist_ok=True)

        # RGB camera thread
        self.cam_record = Process(target=self.record_video_till_stop)

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

        close_time = None

        # Process events
        evt_start_timestamp = None
        for evs in mv_iterator:
            if not evt_start_timestamp:
                # As soon as the event camera starts recording, send a trigger to the
                # rgb thread to throw away previously stored frames.
                evt_start_timestamp = time.time()
                print(f"evt_start_timestamp: {evt_start_timestamp}")

            #print(self.thread_event.is_set())
            if self.thread_event.is_set():
                if close_time is None:
                    close_time = self.get_closing_time()
                    print(f'stopping event camera at {close_time}...')

                # Stop the recording
                #print(datetime.now(), close_time)
                if datetime.now() > close_time:
                    self.device.get_i_events_stream().stop_log_raw_data()
                    self.event_camera_has_stopped.set()
                    print('done')
                    break

    def record_video_till_stop(self):
        #start video capture
        vid_w = 1280
        vid_h = 720
        capture = VideoCaptureAsyncWithTimestamp(src=0, width=vid_w, height=vid_h)
        capture.start()

        frames = 0
        #Create array to hold frames from capture
        images = []
        # Capture for duration defined by variable 'duration'
        prev = datetime.now()
        frame_rate = 30
        fps_delay = timedelta(seconds=0, microseconds=(1/frame_rate)*1000*1000)
        # evt_triggered = False
        start_time = None
        close_time = None
        while True:
            # print('iter')
            time_elapsed = datetime.now() - prev
            ret, new_frame, timestamp = capture.read()

            if time_elapsed > fps_delay and self.event_camera_event.is_set():
                if start_time is None:
                    start_time = datetime.now()
                    print(f"start_time: {start_time}")
                # print(time_elapsed - fps_delay)
                prev = timestamp
                frames += 1
                images.append({'frame': new_frame, 'timestamp': prev})
            if self.thread_event.is_set():
                if close_time is None:
                    close_time = self.get_closing_time()
                    print(f'stopping rgb camera at {close_time}...')
                if datetime.now() > close_time:
                    break
        duration = datetime.now() - start_time
        capture.stop()
        cv2.destroyAllWindows()
        # The fps variable which counts the number of frames and divides it by 
        # the duration gives the frames per second which is used to record the video later.
        print(f"duration: {duration.seconds + duration.microseconds/(1000*1000)}")
        fps = len(images)/(duration.seconds + duration.microseconds/(1000*1000))
        print(f"frames: {len(images)}")
        print(f"fps: {fps}")
        print(f"len(images): {len(images)}")
        print(f"duration: {duration}")
        # The following line initiates the video object and video file named 'video.avi' 
        # of width and height declared at the beginning.
        print("saving video frames")
        # The loop goes through the array of images and writes each image to the video file
        for i in range(len(images)):
            # save video as frames in the frames folder. Add timestamp to filename
            cur_timestamp = images[i]['timestamp']
            if cur_timestamp <= close_time:
                cv2.imwrite(f"{self.log_folder}/frames/frame_{i}_{cur_timestamp.strftime('%H:%M:%S.%f')}.jpg",
                            images[i]['frame'])
            
        images = []
        print("Done")

    def start_recording_rgb_and_event(self):
        self.cam_record.start()
        self.event_camera_event.set()
        self.event_record.start()

    def stop_recording_rgb_and_event(self):
        close_time = datetime.now() + timedelta(seconds=2)
        close_time -= timedelta(microseconds=close_time.microsecond)
        print(f"close_time: {close_time}")
        self.thread_event.set()
        self.cam_record.join()
        self.cam_record.close()

    def get_closing_time(self):
        close_time = datetime.now() + timedelta(seconds=2)
        close_time -= timedelta(microseconds=close_time.microsecond)
        print(f"close_time: {close_time.strftime('%H:%M:%S.%f')}")
        return close_time


rec = Recorder('recordings')
rec.start_recording_rgb_and_event()

# wait 5 seconds
start_time = time.time()

while time.time() - start_time < 5:
    #print('waiting...')
    pass
print('done waiting')

rec.stop_recording_rgb_and_event()