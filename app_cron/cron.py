import requests
import json
import os
import re

def linenotify(message, imagePath=None, stickerPackageId=None, stickerId=None, tk=''):
    url = 'https://notify-api.line.me/api/notify'
    token = os.getenv('LINE_NOTIFY_TOKEN') or (tk or None)
    if token is None:
        print('LINE_NOTIFY_TOKEN is required!')
        return False
    header = {'Authorization': f'Bearer {token}'}
    data = {
        'message': f'[yt-dlp-bot]\n{message}',
        'stickerPackageId': stickerPackageId,
        'stickerId': stickerId,
    }
    file = {'imageFile': open(imagePath,'rb')} if (imagePath) else None
    r = requests.post(url, headers=header, data=data, files=file)
    return r.json()

BASE_PATH = os.getenv('STORAGE_PATH')
API_URL = os.getenv('TURSO_API_URL')

files = [f for f in os.listdir(f'{BASE_PATH}/') if f.endswith('.mp4')]
pattern = r'^(?:live_(\d+)_|(\d+)_)'

print('Files:')
file_dict = {}
for f in files:
    m = re.match(pattern, f)
    if m:
        k = int(m.group(1) or m.group(2))
        print(f'{k}: {f}')
        file_dict[k] = f

liveIds = list(file_dict.keys())
if len(liveIds) == 0:
    print('No files to delete')
    exit()

payload = json.dumps({
  'table': 'member_live',
  'method': 'list',
  'data': None,
  'options': {
    'where': {
      'ids': liveIds
    }
  }
})
headers = {
  'x-api-key': os.getenv('TURSO_API_KEY'),
  'Content-Type': 'application/json'
}

response = requests.request('POST', API_URL, headers=headers, data=payload)
res = response.json().get('result', [])

filtered_data = [item for item in res if item['playback_id']]
id_list = [item['id'] for item in filtered_data]

msg = ''
cnt = 0
for id in id_list:
    if id in file_dict:
        filename = file_dict[id]
        file_path = os.path.join(f'{BASE_PATH}/', filename)
        try:
            os.remove(file_path)
            print(f'Deleted file: {filename}')
            msg += f'{filename}\n'
            cnt += 1
        except OSError as e:
            err = f'Error deleting file: {filename} - {e.strerror}'
            print(err)
            linenotify(err)

linenotify(f'Deleted file: \n{msg}\nTotal: {cnt}')
