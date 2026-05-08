import json

with open('key.json') as f:
    data = json.load(f)

print('[gcp_service_account]')
for k, v in data.items():
    if isinstance(v, str) and '\n' in v:
        print(f'{k} = """{v}"""')
    else:
        print(f'{k} = {json.dumps(v)}')
