# 云盘（`adp volume`）

云盘是空间级的文件存储，应用可以挂载。所有命令都需要 `--space-id`（不传时读 `adp.jsonc`）。

```bash
adp volume create --name 研发资料 --format json            # 名称在空间内唯一
adp volume upload --volume-id <id> --file ./report.pdf --to docs/
adp volume ls --volume-id <id> --path docs --format json
adp volume download --volume-id <id> --path docs/report.pdf --output ./report.pdf
adp volume mv --volume-id <id> --path docs/report.pdf --name report-v2.pdf   # 原地改名
adp volume rm --volume-id <id> --path docs --recursive --yes
```

- 路径相对云盘根目录，不能含 `..`。`--to` 以 `/` 结尾时保留本地文件名。
- 上传不会覆盖已有文件（`VolumeEntryExists`）。要替换时先 `rm` 再上传，并先和用户确认。
- `mv` 用 `--path` 指定原文件、`--name` 给新文件名（只是文件名，不带目录），只能原地改名，不能移动目录或给目录改名。
- 删除目录必须加 `--recursive`。`volume delete` 会删掉云盘里所有文件；先用 `volume get` 看 `referenceApps`，有应用挂载时和用户确认。
- `preview-url --reveal` 输出的是短期可访问的链接，只在用户要时给出，不要写进日志。
