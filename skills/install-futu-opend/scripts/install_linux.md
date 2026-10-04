# Linux 安装步骤（Futu OpenD）

Linux 安装包是 **tar.gz 压缩包**，与 macOS 类似，解压后包含 GUI 版安装包和命令行版。

压缩包内部结构（以 Ubuntu 为例）：
```
Futu_OpenD_x.x.xxxx_Ubuntu/
├── Futu_OpenD-GUI_x.x.xxxx_Ubuntu.deb   ← GUI 版安装包（安装这个）
├── Futu_OpenD_x.x.xxxx_Ubuntu/
│   ├── FutuOpenD                          ← 命令行版主程序（不要运行这个）
│   ├── FutuOpenD.xml                      ← 配置文件
│   └── ...
├── fixrun.sh                              ← 路径修复脚本
└── README.txt
```

## 第一步：下载并解压

**CentOS**：
```bash
curl -L -o ~/Desktop/FutuOpenD.tar.gz "https://www.futunn.com/download/fetch-lasted-link?name=opend-centos"
tar -xzf ~/Desktop/FutuOpenD.tar.gz -C ~/Desktop/
rm ~/Desktop/FutuOpenD.tar.gz
```

**Ubuntu**：
```bash
curl -L -o ~/Desktop/FutuOpenD.tar.gz "https://www.futunn.com/download/fetch-lasted-link?name=opend-ubuntu"
tar -xzf ~/Desktop/FutuOpenD.tar.gz -C ~/Desktop/
rm ~/Desktop/FutuOpenD.tar.gz
```

如果用户通过 `-path` 指定了路径，将 `~/Desktop/` 替换为对应路径。

## 第二步：安装 GUI 版

找到解压后的 GUI 安装包并安装：

**Ubuntu/Debian（.deb）**：
```bash
DEB_PATH=$(find ~/Desktop -maxdepth 3 -name "*OpenD-GUI*.deb" -type f | head -1) && echo "Found: $DEB_PATH"
sudo dpkg -i "$DEB_PATH"
sudo apt-get install -f -y  # 修复依赖
```

**CentOS/RHEL（.rpm）**：
```bash
RPM_PATH=$(find ~/Desktop -maxdepth 3 -name "*OpenD-GUI*.rpm" -type f | head -1) && echo "Found: $RPM_PATH"
sudo rpm -ivh "$RPM_PATH"
```

## 第三步：启动 GUI 版 OpenD

```bash
# 查找已安装的 GUI 版 OpenD
GUI_BIN=$(which Futu_OpenD 2>/dev/null || find /opt /usr/local /usr/bin -name "Futu_OpenD" -type f 2>/dev/null | head -1)
if [ -n "$GUI_BIN" ]; then
    nohup "$GUI_BIN" &
    echo "GUI OpenD started: $GUI_BIN"
else
    echo "GUI OpenD not found. Check installation."
fi
```
