import requests
import xml.etree.ElementTree as tree
import base64
import binascii
import json
from datetime import datetime, timezone
requests.packages.urllib3.disable_warnings()

channels = {
    'stable': 'msedge-stable-win',
    'beta': 'msedge-beta-win',
    'dev': 'msedge-dev-win',
    'canary': 'msedge-canary-win',
}

update_url = 'https://msedge.api.cdp.microsoft.com/api/v1/contents/Browser/namespaces/Default/names/{0}/versions/latest?action=select'
download_url = 'https://msedge.api.cdp.microsoft.com/api/v1/contents/Browser/namespaces/Default/names/{0}/versions/{1}/files?action=GenerateDownloadInfo'

def check_update(appid):
    r= requests.post(update_url.format(appid), data={'targetingAttributes':{'Priority':10, "IsInternalUser":True}}, verify=False)
    return r.json()

def get_download(appid, version):
    r= requests.post(download_url.format(appid, version), verify=False)
    json = r.json()
    fileId = 'MicrosoftEdge_X{0}_{1}.exe'.format(appid[-2:], version)
    for item in json:
        if item['FileId'] == fileId:
            return item
    return json[0]

def get_info(appid):
    res1 = check_update(appid)
    name = res1['ContentId']['Name']
    version = res1['ContentId']['Version']

    res2 = get_download(appid, version)
    size = res2['SizeInBytes']
    sha1 =  base64.b64decode(res2['Hashes']['Sha1']).hex()
    sha256 =  base64.b64decode(res2['Hashes']['Sha256']).hex()
    file = res2['FileId']
    url = res2['Url']
    return name, {'version': version, 'size':size, 'sha1':sha1, 'sha256':sha256, 'file':file, 'url':url}

results = {}

def version_tuple(v):
    return tuple(map(int, (v.split("."))))

def load_json():
    global results
    with open('data.json', 'r') as f:
        results = json.load(f)

def fetch():
    for channel, appid in channels.items():
        for arch in ['x86', 'x64']:
            name, info = get_info(f'{appid}-{arch}')
            if version_tuple(info['version']) <= version_tuple(results[name]['version']):
                print("ignore", name, info['version'])
                continue
            results[name] = info

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

def save_md():
    with open('readme.md', 'w') as f:
        f.write(f'# Automatic Generated Time\n')
        f.write(f'{datetime.now(timezone.utc)}\n')
        f.write('\n')
        f.write(f'# Note\n')
        f.write(f'Microsoft links have an expiration date, so the URL for this project may not actually be available for download\n')
        f.write('\n')
        for name, info in results.items():
            f.write(f'## {name[7:].replace("win-", "").replace("-", " ")}\n')
            f.write(f'**version**:{info["version"]}  \n')
            f.write(f'**size**:{humansize(info["size"])}  \n')
            f.write(f'**sha1**:{info["sha1"]}  \n')
            f.write(f'**sha256**:{info["sha256"]}  \n')
            f.write(f'**file**:{info["file"]}  \n')
            f.write(f'**url**:[{info["url"]}]({info["url"]})  \n')
            f.write('\n')

def save_json():
    with open('data.json', 'w') as f:
        json.dump(results, f, indent=4)
    for k, v in results.items():
        with open(f'{k}.json', 'w') as f:
            json.dump(v, f, indent=4)

def main():
    load_json()
    fetch()
    save_md()
    save_json()

main()
