import base64
import os
import binascii
import json
from datetime import datetime, timezone, timedelta

import requests

requests.packages.urllib3.disable_warnings()

channels = {
    "stable": "msedge-stable-win",
    "win7and8": "msedge-stable-win7and8",
    "beta": "msedge-beta-win",
    "dev": "msedge-dev-win",
    "canary": "msedge-canary-win",
}

check_version_url = (
    "https://msedge.api.cdp.microsoft.com/api/v2/contents/Browser/namespaces/Default/names/{"
    "0}/versions/latest?action=select"
)
get_download_link_url = (
    "https://msedge.api.cdp.microsoft.com/api/v1.1/internal/contents/Browser/namespaces/Default"
    "/names/{0}/versions/{1}/files?action=GenerateDownloadInfo"
)

results = {}


def check_version(appid):
    # 必须包含 UA 头，否则报错
    headers = {"User-Agent": "Microsoft Edge Update/1.3.183.29;winhttp"}
    data = {
        "targetingAttributes": {
            "IsInternalUser": True,
            "Updater": "MicrosoftEdgeUpdate",
            "UpdaterVersion": "1.3.183.29",
        }
    }
    response = requests.post(
        check_version_url.format(appid), json=data, headers=headers, verify=False
    )

    if response.status_code == 200:
        content_id = response.json().get("ContentId")
        if content_id:
            version = content_id.get("Version")
            return version
        else:
            print("ContentId not found in the response.")
    else:
        print(
            "Error: Unable to fetch version information. Status code:",
            response.status_code,
        )

    return None


def get_download_link(appid, version):
    headers = {"User-Agent": "Microsoft Edge Update/1.3.183.29;winhttp"}
    response = requests.post(
        get_download_link_url.format(appid, version), headers=headers, verify=False
    )

    if response.status_code == 200:
        download_info = response.json()
        if download_info:
            # 首先按照字节大小从大到小排序
            download_info.sort(key=lambda x: x.get("SizeInBytes", 0), reverse=True)
            item = download_info[0]
            file_id = item.get("FileId", "")
            url = item.get("Url", "")
            size_in_bytes = item.get("SizeInBytes", 0)
            hashes = item.get("Hashes", {})
            sha1 = hashes.get("Sha1", "")
            sha256 = hashes.get("Sha256", "")

            return {
                "文件名": file_id,
                "下载链接": url,
                "字节大小": size_in_bytes,
                "Sha1": sha1,
                "Sha256": sha256,
            }
        else:
            print("Download information not found in the response.")
    else:
        print(
            "Error: Unable to fetch download information. Status code:",
            response.status_code,
        )

    return None


def get_info(appid):
    version = check_version(appid)
    if version:
        name = appid
        info = get_download_link(appid, version)
        if info:
            info["version"] = version
            return name, info
        else:
            print("Error: Unable to obtain download information for", appid)
    else:
        print("Error: Unable to obtain version information for", appid)
    return None


def version_tuple(v):
    return tuple(map(int, (v.split("."))))


def load_json():
    global results
    if not os.path.exists("data.json"):
        results = {}
        return
    try:
        with open("data.json", "r") as f:
            results = json.load(f)
            if not results:
                results = {}
    except (json.JSONDecodeError, ValueError):
        results = {}


def fetch():
    current_day = datetime.now().day
    for channel, appid in channels.items():
        for arch in ["x86", "x64", "ARM64"]:
            info_result = get_info(f"{appid}-{arch}")
            if info_result is not None:
                name, info = info_result
            else:
                print("Error: Unable to get info for", f"{appid}-{arch}")
            if name not in results:
                results[name] = info
            elif version_tuple(info["version"]) > version_tuple(
                results[name]["version"]
            ):
                results[name] = info
            elif current_day in [2, 11, 20, 28]:
                results[name] = info
            else:
                print("ignore", name, info["version"])


suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def replace_http_to_https():
    for name, info in results.items():
        results[name]["下载链接"] = (
            results[name]
            .get("下载链接", "")
            .replace("http://msedge.b", "https://msedge.sb")
        )


def decode_sha256_base64():
    for name, info in results.items():
        sha256_base64 = info.get("Sha256", "")
        if (
            sha256_base64 and len(sha256_base64) != 64
        ):  # Only decode if not already decoded
            try:
                sha256_decoded = base64.b64decode(sha256_base64).hex()
                results[name]["Sha256"] = sha256_decoded
            except binascii.Error:
                print(f"Error: Unable to decode base64 for {name}")


def save_md():
    index_url = "https://github.com/Bush2021/edge_installer?tab=readme-ov-file#"
    with open("readme.md", "w") as f:
        f.write(f"# Microsoft Edge 离线安装包下载链接（请使用 7-Zip 解压）\n")
        f.write(
            f"稳定版存档：<https://github.com/Bush2021/edge_installer/releases>\n\n"
        )
        f.write(f"## 注意\n")
        f.write(f"* Microsoft 直链会过期，请及时保存。\n")
        f.write(f"* 下载文件名可能是乱码，有需要的话请自行重命名。\n")
        f.write("\n")
        f.write(f"## 目录\n")
        for name in results.keys():
            title = name[7:].replace("win-", "").replace("-", " ")
            link = index_url + title.replace(" ", "-")
            f.write(f"* [{title}]({link})\n")
        f.write("\n")
        for name, info in results.items():
            f.write(f'## {name[7:].replace("win-", "").replace("-", " ")}\n')
            f.write(f'**最新版本**：{info.get("version", "")}  \n')
            f.write(f'**文件大小**：{humansize(info.get("字节大小", 0))}  \n')
            f.write(f'**文件名**：{info.get("文件名", "")}  \n')
            f.write(f'**校验值（Sha256）**：{info.get("Sha256", "")}  \n')
            f.write(
                f'**下载链接**：[{info.get("下载链接", "")}]({info.get("下载链接", "")})  \n'
            )
            f.write("\n")


def save_json():
    with open("data.json", "w") as f:
        json.dump(results, f, indent=4)


def main():
    load_json()
    fetch()
    replace_http_to_https()
    decode_sha256_base64()
    save_md()
    save_json()


if __name__ == "__main__":
    main()
