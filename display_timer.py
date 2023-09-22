import datetime
import time

while True:
    date = datetime.datetime.now()
    # print date up to milliseconds
    print(date.strftime('%H:%M:%S.%f'))
    time.sleep(0.0001)