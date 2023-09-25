from recorder_api import Recorder
import time

rec = Recorder('recordings')

time.sleep(3)

rec.start_recording_rgb_and_event()

# wait 5 seconds
start_time = time.time()

while time.time() - start_time < 15:
    #print('waiting...')
    pass
print('done waiting')

rec.stop_recording_rgb_and_event()

time.sleep(3)