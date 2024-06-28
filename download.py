import json
import os

import requests


def version_tuple(v):
    return tuple(map(int, (v.split("."))))


def get_last_download():
    try:
        with open('last_download.txt', 'r') as file:
            last_version = file.read().strip()
            return last_version
    except FileNotFoundError:
        return ''


def check_update():
    last_version = get_last_download()
    with open('data.json', 'r') as f:
        data = json.load(f)
        current_version = data['msedge-stable-win-x64']['version']
    if version_tuple(last_version) < version_tuple(current_version):
        with open('last_download.txt', 'w') as file:
            file.write(current_version)
        return True
    else:
        return False


def get_download_url(version):
    with open('data.json', 'r') as f:
        data = json.load(f)
        download_url = data[version]['下载链接']
    return download_url


def get_filename(version):
    with open('data.json', 'r') as f:
        data = json.load(f)
        filename = data[version]['文件名']
    return filename


def download_file(url, name):
    if os.path.exists(name):
        print(f'The file {name} already exists, skip downloading')
        return
    r = requests.get(url, stream=True)
    with open(name, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print('Download complete')


def download():
    versions = ['msedge-stable-win-x86', 'msedge-stable-win-x64', 'msedge-stable-win-ARM64']
    if check_update():
        print('New version detected, start downloading...')
        for version in versions:
            download_file(get_download_url(version), get_filename(version))
        if os.path.exists('__pycache__'):
            os.system('rmdir /s /q __pycache__')
    else:
        print('No new version detected, skip downloading')
        return


if __name__ == '__main__':
    download()
