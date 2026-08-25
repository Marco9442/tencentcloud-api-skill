#!/usr/bin/env python3
"""Synchronize the official ClawHub tencentcloud-api-skill package."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import urllib.request
import zipfile

OWNER = "tencent-adm"
SLUG = "tencentcloud-api-skill"
UPSTREAM_URL = f"https://clawhub.ai/{OWNER}/skills/{SLUG}"
API_URL = f"https://clawhub.ai/api/v1/skills/{SLUG}"
DOWNLOAD_URL = f"https://clawhub.ai/api/v1/download?slug={SLUG}&tag=latest"
ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".clawhub" / "upstream.json"
MIRROR_OWNED = {
    "README.md",
    "scripts/sync_upstream.py",
    ".github/workflows/sync-upstream.yml",
    ".clawhub/upstream.json",
}
MIT_0 = """MIT No Attribution

Copyright {year} Tencent

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the \"Software\"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Marco9442/tencentcloud-api-skill sync workflow"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members: list[zipfile.ZipInfo] = []
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        if info.is_dir():
            continue
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise RuntimeError(f"Unsafe path in upstream archive: {info.filename!r}")
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"Symlink is not allowed in upstream archive: {info.filename!r}")
        normalized = path.as_posix()
        if normalized in MIRROR_OWNED or normalized.startswith((".git/", ".github/", "scripts/", ".clawhub/")):
            raise RuntimeError(f"Upstream archive conflicts with mirror infrastructure: {normalized}")
        members.append(info)
    return members


def read_previous_files() -> list[str]:
    if not STATE_PATH.exists():
        return []
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return [entry["path"] for entry in state.get("files", [])]


def remove_previous_files(paths: list[str]) -> None:
    for relative in sorted(paths, key=lambda value: len(PurePosixPath(value).parts), reverse=True):
        if relative in MIRROR_OWNED:
            continue
        target = ROOT / relative
        if target.is_file() or target.is_symlink():
            target.unlink()
    for directory in sorted(
        {str(PurePosixPath(path).parent) for path in paths},
        key=lambda value: len(PurePosixPath(value).parts),
        reverse=True,
    ):
        if directory == ".":
            continue
        target = ROOT / directory
        try:
            target.rmdir()
        except (FileNotFoundError, OSError):
            pass


def copy_upstream_files(archive: zipfile.ZipFile, members: list[zipfile.ZipInfo]) -> list[dict[str, str | int]]:
    records: list[dict[str, str | int]] = []
    for info in sorted(members, key=lambda item: item.filename):
        relative = PurePosixPath(info.filename).as_posix()
        data = archive.read(info)
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        )
    return records


def content_digest(records: list[dict[str, str | int]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(str(record["path"]).encode())
        digest.update(b"\0")
        digest.update(str(record["sha256"]).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def write_license(license_id: str, published_at_ms: int, upstream_paths: set[str]) -> None:
    if "LICENSE" in upstream_paths or "LICENSE.txt" in upstream_paths or "LICENSE.md" in upstream_paths:
        return
    if license_id != "MIT-0":
        raise RuntimeError(f"Unsupported license without a bundled license file: {license_id!r}")
    year = __import__("datetime").datetime.fromtimestamp(published_at_ms / 1000, tz=__import__("datetime").timezone.utc).year
    (ROOT / "LICENSE").write_text(MIT_0.format(year=year), encoding="utf-8")


def write_readme(version: str, license_id: str) -> None:
    readme = f"""# tencentcloud-api-skill

[![Sync ClawHub upstream](https://github.com/Marco9442/tencentcloud-api-skill/actions/workflows/sync-upstream.yml/badge.svg)](https://github.com/Marco9442/tencentcloud-api-skill/actions/workflows/sync-upstream.yml)

这是 ClawHub 官方技能 [`{OWNER}/{SLUG}`]({UPSTREAM_URL}) 的**自动同步公开镜像**。仓库根目录保持标准 Agent Skill 结构，可直接作为 GitHub Skill 源使用。

## 上游信息

- ClawHub 上游：[`{OWNER}/{SLUG}`]({UPSTREAM_URL})
- 当前同步版本：`{version}`
- 上游许可证：`{license_id}`
- 上游元数据：[`{API_URL}`]({API_URL})
- 最新版下载：[`{DOWNLOAD_URL}`]({DOWNLOAD_URL})
- 同步清单：[`.clawhub/upstream.json`](.clawhub/upstream.json)

> 本仓库不是独立开发分支。`SKILL.md`、`skill-card.md`、`references/`、`_meta.json` 等技能文件来自 ClawHub 上游；镜像仅增加 README、许可证副本、来源清单和自动同步基础设施。

## 作为 Agent Skill 使用

将本仓库作为 GitHub Skill 源安装，或克隆到 Agent 的 skills 目录。入口文件位于仓库根目录：

```text
SKILL.md
```

示例：

```bash
git clone https://github.com/Marco9442/tencentcloud-api-skill.git
```

具体安装方式取决于所使用的 Agent 运行时；任何支持标准 `SKILL.md` 仓库布局的运行时都可以直接读取本仓库。

## 自动同步机制

GitHub Actions 工作流 [`.github/workflows/sync-upstream.yml`](.github/workflows/sync-upstream.yml) 会：

1. 每 6 小时检查一次 ClawHub `latest` 版本，也支持手动触发。
2. 从 ClawHub API 核验所有者、slug、版本和许可证。
3. 安全解压官方发布包，并同步新增、修改和删除的上游文件。
4. 更新当前版本、许可证和 `.clawhub/upstream.json` 文件哈希清单。
5. 仅当 Git 工作区实际发生变化时创建并推送提交；无变化时正常结束且不产生空提交。

同步提交由 `github-actions[bot]` 创建，提交信息格式为：

```text
chore(sync): update ClawHub upstream to <version>
```

## 来源与许可证

原始来源和上游版本信息保存在 [`.clawhub/upstream.json`](.clawhub/upstream.json)。上游 API 声明当前版本采用 `{license_id}`；许可证文本见 [`LICENSE`](LICENSE)。所有上游内容的权利归原作者及权利人所有。
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    metadata = json.loads(fetch(API_URL))
    skill = metadata["skill"]
    owner = metadata["owner"]
    latest = metadata["latestVersion"]
    if skill["slug"] != SLUG or owner["handle"] != OWNER:
        raise RuntimeError(
            f"Unexpected upstream identity: {owner['handle']}/{skill['slug']}"
        )

    version = str(latest["version"])
    license_id = str(latest["license"])
    published_at = int(latest["createdAt"])
    package = fetch(DOWNLOAD_URL)

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        members = safe_members(archive)
        names = {PurePosixPath(info.filename).as_posix() for info in members}
        if "SKILL.md" not in names or "_meta.json" not in names:
            raise RuntimeError("Upstream package is missing SKILL.md or _meta.json")
        package_meta = json.loads(archive.read("_meta.json"))
        if package_meta.get("slug") != SLUG or str(package_meta.get("version")) != version:
            raise RuntimeError(
                f"API/package mismatch: API={version}, package={package_meta!r}"
            )

        remove_previous_files(read_previous_files())
        records = copy_upstream_files(archive, members)

    upstream_paths = {str(record["path"]) for record in records}
    write_license(license_id, published_at, upstream_paths)
    write_readme(version, license_id)

    state = {
        "schemaVersion": 1,
        "owner": OWNER,
        "slug": SLUG,
        "version": version,
        "license": license_id,
        "publishedAt": published_at,
        "upstreamUrl": UPSTREAM_URL,
        "apiUrl": API_URL,
        "downloadUrl": DOWNLOAD_URL,
        "contentSha256": content_digest(records),
        "files": records,
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Synced {OWNER}/{SLUG} version {version} ({len(records)} files)")


if __name__ == "__main__":
    main()
