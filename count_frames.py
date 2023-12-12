from glob import glob

frames = glob('recordings/*/*/*/*.jpg')

print(f'Num frames: {len(frames)}')
print(f'Seconds: {len(frames)/30}')
print(f'Hours: {len(frames)/30/3600}')
