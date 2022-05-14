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
    r= requests.post(update_url.format(appid), data={'targetingAttributes':{'Priority':10}}, verify=False)
    return r.json()

def get_download(appid, version):
    r= requests.post(download_url.format(appid, version), verify=False)
    return r.json()

def get_info(appid):
    res1 = check_update(appid)
    name = res1['ContentId']['Name']
    version = res1['ContentId']['Version']

    res2 = get_download(appid, version)[0]
    size = res2['SizeInBytes']
    sha1 =  base64.b64decode(res2['Hashes']['Sha1']).hex()
    sha256 =  base64.b64decode(res2['Hashes']['Sha256']).hex()
    file = res2['FileId']
    url = res2['Url']
    return {'name':name, 'version': version, 'size':size, 'sha1':sha1, 'sha256':sha256, 'file':file, 'url':url}

results = []

def fetch():
    for channel, appid in channels.items():
        for arch in ['x86', 'x64']:
            info = get_info(f'{appid}-{arch}')
            results.append(info)

def save_md():
    with open('readme.md', 'w') as f:
        f.write(f'# Automatic Generated Time\n')
        f.write(f'{datetime.now(timezone.utc)}\n')
        f.write('\n')
        f.write(f'# Note\n')
        f.write(f'Microsoft links have an expiration date, so the URL for this project is not actually downloadable\n')
        f.write('\n')
        for info in results:
            f.write(f'## {info["name"][7:].replace("win-", "")}\n')
            f.write(f'version:{info["version"]}  \n')
            f.write(f'size:{info["size"]}  \n')
            f.write(f'sha1:{info["sha1"]}  \n')
            f.write(f'sha256:{info["sha256"]}  \n')
            f.write(f'file:{info["file"]}  \n')
            f.write(f'url:[{info["url"]}]({info["url"]})  \n')
            f.write('\n')

def main():
    fetch()
    save_md()

main()
