# MicroPython package installer
# MIT license; Copyright (c) 2022 Jim Mussared

import aiohttpclient as aiohttp
import sys


_PACKAGE_INDEX = const("https://micropython.org/pi/v2")
_CHUNK_SIZE = 128
_DEBUG = False


# This implements os.makedirs(os.dirname(path))
def _ensure_path_exists(path):
    import os

    split = path.split("/")

    # Handle paths starting with "/".
    if not split[0]:
        split.pop(0)
        split[0] = "/" + split[0]

    prefix = ""
    for i in range(len(split) - 1):
        prefix += split[i]
        try:
            os.stat(prefix)
        except:
            os.mkdir(prefix)
        prefix += "/"


# Copy from src (stream) to dest (function-taking-bytes)
async def _chunk(src, dest):
    buf = memoryview(bytearray(_CHUNK_SIZE))
    while True:
        n = await src.readinto(buf)
        if n == 0:
            break
        dest(buf if n == _CHUNK_SIZE else buf[:n])


# Check if the specified path exists and matches the hash.
async def _check_exists(path, short_hash):
    try:
        import binascii
        import hashlib

        with open(path, "rb") as f:
            hs256 = hashlib.sha256()
            await _chunk(f, hs256.update)
            existing_hash = str(
                binascii.hexlify(hs256.digest())[: len(short_hash)], "utf-8"
            )
            return existing_hash == short_hash
    except:
        return False


def _rewrite_url(url, branch=None):
    if not branch:
        branch = "HEAD"
    if url.startswith("github:"):
        url = url[7:].split("/")
        url = (
            "https://raw.githubusercontent.com/"
            + url[0]
            + "/"
            + url[1]
            + "/"
            + branch
            + "/"
            + "/".join(url[2:])
        )
    return url


async def _download_file(url, dest):
    if _DEBUG:
        print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                if _DEBUG:
                    print("Error", response.status, "requesting", url)
                return False
            if _DEBUG:
                print("Copying:", dest)
            _ensure_path_exists(dest)
            with open(dest, "wb") as f:
                await _chunk(response.content, f.write)

            return True


async def _install_json(package_json_url, index, target, version, mpy):
    package_json = await _fetch_json(package_json_url, index, target, version, mpy)
    for target_path, short_hash in package_json.get("hashes", ()):
        fs_target_path = target + "/" + target_path
        if await _check_exists(fs_target_path, short_hash):
            if _DEBUG:
                print("Exists:", fs_target_path)
        else:
            file_url = "{}/file/{}/{}".format(index, short_hash[:2], short_hash)
            if not await _download_file(file_url, fs_target_path):
                if _DEBUG:
                    print("File not found: {} {}".format(target_path, short_hash))
                return False
    for target_path, url in package_json.get("urls", ()):
        fs_target_path = target + "/" + target_path
        if not await _download_file(_rewrite_url(url, version), fs_target_path):
            if _DEBUG:
                print("File not found: {} {}".format(target_path, url))
            return False
    for dep, dep_version in package_json.get("deps", ()):
        if not await _install_package(dep, index, target, dep_version, mpy):
            return False
    return True


async def _install_package(package, index, target, version, mpy):
    if (
        package.startswith("http://")
        or package.startswith("https://")
        or package.startswith("github:")
    ):
        if package.endswith(".py") or package.endswith(".mpy"):
            if _DEBUG:
                print("Downloading {} to {}".format(package, target))
            return await _download_file(
                _rewrite_url(package, version), target + "/" + package.rsplit("/")[-1]
            )
        else:
            if not package.endswith(".json"):
                if not package.endswith("/"):
                    package += "/"
                package += "package.json"
            if _DEBUG:
                print("Installing {} to {}".format(package, target))
    else:
        if not version:
            version = "latest"
        if _DEBUG:
            print(
                "Installing {} ({}) from {} to {}".format(
                    package, version, index, target
                )
            )

        mpy_version = (
            sys.implementation._mpy & 0xFF
            if mpy and hasattr(sys.implementation, "_mpy")
            else "py"
        )

        package = "{}/package/{}/{}/{}.json".format(
            index, mpy_version, package, version
        )

    return await _install_json(package, index, target, version, mpy)


async def install(package, index=None, target=None, version=None, mpy=True):
    if not target:
        for p in sys.path:
            if p.endswith("/lib"):
                target = p
                break
        else:
            if _DEBUG:
                print("Unable to find lib dir in sys.path")
            return

    if not index:
        index = _PACKAGE_INDEX

    if await _install_package(package, index.rstrip("/"), target, version, mpy):
        if _DEBUG:
            print("Done")
        return True
    else:
        if _DEBUG:
            print("Package may be partially installed")


async def _fetch_json(package_json_url, index, target, version, mpy):
    async with aiohttp.ClientSession() as session:
        async with session.get(_rewrite_url(package_json_url, version)) as resp:
            package_json = {}
            if resp.status != 200:
                if _DEBUG:
                    print("Package not found:", package_json_url)
                return False

            package_json = await resp.json()
    return package_json


async def _fetch_package(package, index, target, version, mpy):
    if (
        package.startswith("http://")
        or package.startswith("https://")
        or package.startswith("github:")
    ):
        if not package.endswith(".json"):
            if not package.endswith("/"):
                package += "/"
            package += "package.json"

        if _DEBUG:
            print("Fetching {} ...".format(package))
    else:
        if not version:
            version = "latest"

        if _DEBUG:
            print(
                "Fetching {} ({}) from {} ...".format(
                    package,
                    version,
                    index,
                )
            )

        mpy_version = (
            sys.implementation._mpy & 0xFF
            if mpy and hasattr(sys.implementation, "_mpy")
            else "py"
        )

        package = "{}/package/{}/{}/{}.json".format(
            index, mpy_version, package, version
        )

    return await _fetch_json(package, index, target, version, mpy)


async def fetch(package, index=None, target=None, version=None, mpy=True):
    if not target:
        for p in sys.path:
            if p.endswith("/lib"):
                target = p
                break
        else:
            if _DEBUG:
                print("Unable to find lib dir in sys.path")
            return

    if not index:
        index = _PACKAGE_INDEX

    pack = await _fetch_package(package, index.rstrip("/"), target, version, mpy)
    if pack:
        if _DEBUG:
            print("Done")
    else:
        if _DEBUG:
            print("Package may be partially installed")
    return pack
