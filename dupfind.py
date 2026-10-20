#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections import defaultdict

CHUNK_SIZE = 1024 * 1024
PROGRESS_EVERY = 200


def parse_min_size(text: str) -> int:
    raw = text.strip().lower().replace(" ", "")
    if not raw:
        raise ValueError("empty")
    units = (("gb", 1024 ** 3), ("mb", 1024 ** 2), ("kb", 1024))
    multiplier = 1
    number = raw
    for suffix, value in units:
        if raw.endswith(suffix):
            number = raw[: -len(suffix)]
            multiplier = value
            break
    if not number.isdigit():
        raise ValueError(raw)
    return int(number) * multiplier


def format_bytes(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n / (1024 ** 3):.1f} GB"
    if n >= 1024 ** 2:
        return f"{n / (1024 ** 2):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} 字节"


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def scan(root: str, min_size: int) -> tuple[dict[int, list[str]], int, int]:
    size_groups: dict[int, list[str]] = defaultdict(list)
    scanned = 0
    skipped = 0

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [
            name
            for name in dirnames
            if not os.path.islink(os.path.join(dirpath, name))
        ]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                continue
            try:
                if not os.path.isfile(path):
                    continue
                size = os.path.getsize(path)
            except OSError:
                skipped += 1
                continue

            scanned += 1
            if scanned % PROGRESS_EVERY == 0:
                print(f"已扫描 {scanned} 个文件...", file=sys.stderr)

            if size == 0 or size < min_size:
                continue
            size_groups[size].append(os.path.abspath(path))

    return size_groups, scanned, skipped


def find_duplicate_groups(
    size_groups: dict[int, list[str]],
) -> tuple[list[tuple[int, int, list[str]]], int]:
    groups: list[tuple[int, int, list[str]]] = []
    skipped = 0

    for size, paths in size_groups.items():
        if len(paths) < 2:
            continue
        hashes: dict[str, list[str]] = defaultdict(list)
        for path in paths:
            try:
                digest = sha256_file(path)
            except OSError:
                skipped += 1
                continue
            hashes[digest].append(path)
        for same_paths in hashes.values():
            if len(same_paths) < 2:
                continue
            wasted = (len(same_paths) - 1) * size
            groups.append((wasted, size, same_paths))

    groups.sort(key=lambda item: item[0], reverse=True)
    return groups, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dupfind.py",
        description="找出内容完全相同的重复文件。默认只查看，不删除。",
    )
    parser.add_argument("path", metavar="文件夹路径", help="要扫描的文件夹")
    parser.add_argument(
        "--min-size",
        default="1",
        metavar="大小",
        help="忽略小于该大小的文件，例如 1kb、1mb、1gb",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        min_size = parse_min_size(args.min_size)
    except ValueError:
        print(f"无效的 --min-size：{args.min_size}", file=sys.stderr)
        return 2

    root = os.path.abspath(args.path)
    if not os.path.exists(root):
        print(f"路径不存在：{root}", file=sys.stderr)
        return 2
    if not os.path.isdir(root):
        print(f"不是文件夹：{root}", file=sys.stderr)
        return 2

    try:
        size_groups, scanned, skipped_scan = scan(root, min_size)
        groups, skipped_hash = find_duplicate_groups(size_groups)
    except Exception as exc:  # noqa: BLE001
        print(f"运行失败：{exc}", file=sys.stderr)
        return 1

    skipped = skipped_scan + skipped_hash
    if not groups:
        print("没有发现重复文件")
        if scanned or skipped:
            print(f"扫描完成：{scanned} 个文件，跳过 {skipped} 个")
        return 0

    wasted_total = sum(item[0] for item in groups)
    print(
        f"扫描完成：{scanned} 个文件，跳过 {skipped} 个，"
        f"发现 {len(groups)} 组重复，多占 {format_bytes(wasted_total)}"
    )
    print()
    for index, (wasted, size, paths) in enumerate(groups, start=1):
        print(f"[{index}] 每个 {format_bytes(size)}，共 {len(paths)} 个")
        for path in paths:
            print(f"  {path}")
        if index != len(groups):
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
