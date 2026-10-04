#!/usr/bin/env python3
"""准备本 Skill 的计算脚本（优先用包内脚本，缺失时下载，之后复用）。

WorkBuddy Skill 包有解压体积上限（见 skill-package.cjs 的 MAX_UNPACKED_BYTES），
因此确定性计算脚本（calculate/render/word_report/preflight_narrative/verify）
在打 zip 包时被排除，改为运行时下载到沙箱目录后执行。

以目录形式分发的渠道（如专家团）不受该体积限制，脚本可直接内联在 scripts/ 下；
此时优先使用包内脚本，不产生任何网络请求。

用法：
    python3 /workspace/.codebuddy/skills/dd-financial-analysis/scripts/bootstrap.py

输出 JSON（stdout）：
    {"ok": true, "scripts_dir": "/workspace/.aidd/dd-financial-analysis/scripts", "cached": false}
    {"ok": false, "error": "..."}

后续所有脚本调用都使用返回的 scripts_dir，例如：
    python3 <scripts_dir>/calculate.py < input.json

幂等：已存在且校验通过时直接复用，不重复下载。
"""

import json
import os
import shutil
import sys
import urllib.request
import zipfile

BUNDLE_URL = os.environ.get(
    'AIDD_FINANCE_SCRIPTS_URL',
    'https://caiclaw-dev.cos.txtfc.cloud/system/wb-skills/dd-financial-analysis-scripts.zip',
)
TARGET_DIR = os.environ.get(
    'AIDD_FINANCE_SCRIPTS_DIR', '/workspace/.aidd/dd-financial-analysis/scripts'
)
REQUIRED = (
    'calculate.py',
    'render.py',
    'tables.py',
    'word_report.py',
    'md_to_docx.py',
    'preflight_narrative.py',
    'verify.py',
)
TIMEOUT = 60


def _complete(directory: str) -> bool:
    return all(os.path.isfile(os.path.join(directory, name)) for name in REQUIRED)


def main() -> None:
    # 包内已内联脚本（目录分发渠道，如专家团）→ 直接复用，不产生网络请求。
    # Skill 包分发时这些脚本已被打包工具排除，此处检测不到，自然回退到下载。
    bundled_dir = os.path.dirname(os.path.abspath(__file__))
    if _complete(bundled_dir):
        print(
            json.dumps(
                {'ok': True, 'scripts_dir': bundled_dir, 'cached': True, 'source': 'bundled'},
                ensure_ascii=False,
            )
        )
        return

    if _complete(TARGET_DIR):
        print(json.dumps({'ok': True, 'scripts_dir': TARGET_DIR, 'cached': True}, ensure_ascii=False))
        return

    archive = TARGET_DIR + '.zip'
    os.makedirs(os.path.dirname(TARGET_DIR) or '.', exist_ok=True)
    try:
        with urllib.request.urlopen(BUNDLE_URL, timeout=TIMEOUT) as response:
            payload = response.read()
        with open(archive, 'wb') as handle:
            handle.write(payload)

        staging = TARGET_DIR + '.staging'
        shutil.rmtree(staging, ignore_errors=True)
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.namelist():
                # 拒绝绝对路径与目录穿越条目
                if member.startswith('/') or '..' in member.split('/'):
                    raise ValueError(f'压缩包含非法路径条目: {member}')
            bundle.extractall(staging)

        if not _complete(staging):
            missing = [n for n in REQUIRED if not os.path.isfile(os.path.join(staging, n))]
            raise ValueError(f'脚本包缺少文件: {", ".join(missing)}')

        shutil.rmtree(TARGET_DIR, ignore_errors=True)
        os.replace(staging, TARGET_DIR)
    except Exception as exc:  # noqa: BLE001 — 需把任意失败原因原样报给 Agent
        print(
            json.dumps(
                {'ok': False, 'error': f'{type(exc).__name__}: {exc}', 'url': BUNDLE_URL},
                ensure_ascii=False,
            )
        )
        sys.exit(1)
    finally:
        if os.path.exists(archive):
            os.remove(archive)

    print(json.dumps({'ok': True, 'scripts_dir': TARGET_DIR, 'cached': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
