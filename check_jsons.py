from glob import glob
import json

json_paths = glob('./recordings/*/user_data.json')

for jp in json_paths:
    with open(jp,'r') as f:
        data = json.load(f)
        print(f"\n{data['name']}, {data['surname']}, {data['email']}, {data['user_hash']} ")

