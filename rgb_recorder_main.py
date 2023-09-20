# Import the recording process
from camera_record import record_video
# set recording duration
record_time = 20
# To run this as part of a bigger program, use mutltiprocessing to create a seperate process 
# for video recording using the following lines.
from multiprocessing import Process
# The line above can go to the top of your file and the following lines should be placed 
# where ever you need to record a video
# Create the process thread object
cam_record = Process(target = record_video, args = (record_time, ))
cam_record.start()
# The following statement waits till the process is completed before going to the next line of code
cam_record.join()
cam_record.close()
# If recording a video is not part of a bigger program then you don't need to use multiprocesing 
# and can comment out the last 4 lines and uncomment the next line
#record_time(record_time)