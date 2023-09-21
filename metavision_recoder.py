# Copyright (c) Prophesee S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

"""
Sample code that demonstrates how to use Metavision SDK to record events from a live camera in a RAW file
"""
import sys
print(sys.path)
# Add /usr/lib/python3/dist-packages/ to PYTHONPATH if the output of print(sys.path) does not mention it.
sys.path.append("/usr/lib/python3/dist-packages/")
from metavision_core.event_io.raw_reader import initiate_device
from metavision_core.event_io import EventsIterator
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
import argparse
import time
import os
from multiprocessing import Process, Event


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Metavision RAW file Recorder sample.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-o', '--output-dir', default="", help="Directory where to create RAW file with recorded event data")
    args = parser.parse_args()
    return args


def record(device, args, process_event):

    start = time.time()

    # Start the recording
    if device.get_i_events_stream():
        log_path = "recording_" + time.strftime("%y%m%d_%H%M%S", time.localtime()) + ".raw"
        if args.output_dir != "":
            log_path = os.path.join(args.output_dir, log_path)
        print(f'Recording to {log_path}')
        device.get_i_events_stream().log_raw_data(log_path)

    # Events iterator on Device
    mv_iterator = EventsIterator.from_device(device=device)
    height, width = mv_iterator.get_size()  # Camera Geometry

    # Process events
    for evs in mv_iterator:
        # Dispatch system events to the window
        #EventLoop.poll_and_dispatch()
    
        if process_event.is_set():
            # Stop the recording
            device.get_i_events_stream().stop_log_raw_data()
            break
    

def main():
    """ Main """
    args = parse_args()

    process_event = Event()
    device = initiate_device("")
    record_process = Process(target=record, args=(device, args, process_event))
    record_process.start()
    start_time = time.time()

    while time.time() - start_time < 5:
        pass

    process_event.set()

    record_process.join()
    record_process.close()

if __name__ == "__main__":
    main()