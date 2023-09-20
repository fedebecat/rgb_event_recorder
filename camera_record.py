import cv2
# Import the video capturing function
from video_capture import VideoCaptureAsync
import time

#Specify width and height of video to be recorded
vid_w = 1280
vid_h = 720
#Intiate Video Capture object
capture = VideoCaptureAsync(src=0, width=vid_w, height=vid_h)
#Intiate codec for Video recording object
fourcc = cv2.VideoWriter_fourcc(*'DIVX')

def record_video_till_stop(thread_event, evt_camera_trigger, log_folder):
    #start video capture
    capture.start()

    frames = 0
    #Create array to hold frames from capture
    images = []
    # Capture for duration defined by variable 'duration'
    prev = 0
    frame_rate = 30
    start_time = time.time()
    evt_triggered = False
    while True:
        if evt_camera_trigger.is_set() and not evt_triggered:
            # reset buffer as soon as the event camera is ready
            images = []
            evt_triggered = True
        time_elapsed = time.time() - prev
        ret, new_frame = capture.read()
        if time_elapsed > 1./frame_rate:
            prev = time.time()
            frames += 1
            images.append({'frame': new_frame, 'timestamp': prev})
        if thread_event.is_set():
            break
    duration = time.time() - start_time
    capture.stop()
    cv2.destroyAllWindows()
    # The fps variable which counts the number of frames and divides it by 
    # the duration gives the frames per second which is used to record the video later.
    fps = frames/duration
    print(f"frames: {frames}")
    print(f"fps: {fps}")
    print(f"len(images): {len(images)}")
    print(f"duration: {duration}")
    # The following line initiates the video object and video file named 'video.avi' 
    # of width and height declared at the beginning.
    #out = cv2.VideoWriter('video.avi', fourcc, fps, (vid_w,vid_h))
    print("saving video frames")
    # The loop goes through the array of images and writes each image to the video file
    for i in range(len(images)):
        #out.write(images[i]['frame'])
        # save video as frames in the frames folder. Add timestamp to filename
        cv2.imwrite(f"{log_folder}/frames/frame_{i}_{images[i]['timestamp']}.jpg", images[i]['frame'])
        
    images = []
    print("Done")


def record_video(duration):
    #start video capture
    capture.start()
    time_end = time.time() + duration

    frames = 0
    #Create array to hold frames from capture
    images = []
    # Capture for duration defined by variable 'duration'
    prev = 0
    frame_rate = 30
    while time.time() <= time_end:
        
        time_elapsed = time.time() - prev
        ret, new_frame = capture.read()
        if time_elapsed > 1./frame_rate:
            prev = time.time()
            frames += 1
            images.append(new_frame)
            # Create a full screen video display. Comment the following 2 lines if you have a specific dimension 
            # of display window in mind and don't mind the window title bar.
            #cv2.namedWindow('image',cv2.WND_PROP_FULLSCREEN)
            #cv2.setWindowProperty('image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            # Here only every 5th frame is shown on the display. Change the '5' to a value suitable to the project. 
            # The higher the number, the more processing required and the slower it becomes
            if False: #frames ==0 or frames%5 == 0:
                # This project used a Pitft screen and needed to be displayed in fullscreen. 
                # The larger the frame, higher the processing and slower the program.
                # Uncomment the following line if you have a specific display window in mind. 
                #frame = cv2.resize(new_frame,(640,480))
                frame = cv2.flip(new_frame,180)
                cv2.imshow('frame', frame)
        #if cv2.waitKey(1) & 0xFF == ord('q'):
        #    break
    capture.stop()
    cv2.destroyAllWindows()
    # The fps variable which counts the number of frames and divides it by 
    # the duration gives the frames per second which is used to record the video later.
    fps = frames/duration
    print(frames)
    print(fps)
    print(len(images)) 
    # The following line initiates the video object and video file named 'video.avi' 
    # of width and height declared at the beginning.
    out = cv2.VideoWriter('video.avi', fourcc, fps, (vid_w,vid_h))
    print("creating video")
    # The loop goes through the array of images and writes each image to the video file
    for i in range(len(images)):
        out.write(images[i])
    images = []
    print("Done")