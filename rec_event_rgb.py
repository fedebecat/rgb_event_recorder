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


def main():
    """ Main """
    output_dir = 'recordings'
    # HAL Device on live camera
    device = initiate_device("")
    #record_time = 5
    thread_event = Event()
    event_camera_event = Event()
    recording_name = "recording_" + time.strftime("%y%m%d_%H%M%S", time.localtime())
    log_folder = os.path.join(output_dir, recording_name)
    os.makedirs(log_folder, exist_ok=True)
    os.makedirs(log_folder + '/frames', exist_ok=True)
    cam_record = Process(target = record_video_till_stop, args = (thread_event, event_camera_event, log_folder))

    # Start the recording
    if device.get_i_events_stream():
        # create folder
        log_path = log_folder + "/event.raw"
        print(f'Recording to {log_path}')
        device.get_i_events_stream().log_raw_data(log_path)

    # Events iterator on Device
    mv_iterator = EventsIterator.from_device(device=device)
    height, width = mv_iterator.get_size()  # Camera Geometry

    # Window - Graphical User Interface
    with MTWindow(title="Metavision Events Viewer", width=width, height=height,
                  mode=BaseWindow.RenderMode.BGR) as window:
        def keyboard_cb(key, scancode, action, mods):
            if key == UIKeyEvent.KEY_ESCAPE or key == UIKeyEvent.KEY_Q:
                window.set_close_flag()

        window.set_keyboard_callback(keyboard_cb)

        # Event Frame Generator
        event_frame_gen = PeriodicFrameGenerationAlgorithm(sensor_width=width, sensor_height=height, fps=25,
                                                           palette=ColorPalette.Dark)

        def on_cd_frame_cb(ts, cd_frame):
            window.show_async(cd_frame)

        event_frame_gen.set_output_callback(on_cd_frame_cb)

        cam_record.start()

        evt_start_timestamp = None
        startup_time = True
        startup_counter = 0
        startup_limit = 5
        # Process events
        for evs in mv_iterator:
            if startup_time:
                startup_counter += 1
                if startup_counter > startup_limit:
                    startup_time = False
                    print("startup time over")
                print('skipping events')
                continue
                
            if not evt_start_timestamp:
                event_camera_event.set()
                evt_start_timestamp = time.time()
                print(f"evt_start_timestamp: {evt_start_timestamp}")
            # Dispatch system events to the window
            EventLoop.poll_and_dispatch()
            event_frame_gen.process_events(evs)

            if window.should_close():
                # Stop the recording
                device.get_i_events_stream().stop_log_raw_data()

                thread_event.set()
                cam_record.join()
                cam_record.close()
                break


if __name__ == "__main__":
    main()