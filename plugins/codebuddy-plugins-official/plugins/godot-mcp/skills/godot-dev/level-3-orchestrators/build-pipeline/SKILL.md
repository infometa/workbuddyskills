---
name: build-pipeline
description: >
  构建流水线技能。管理项目的导出、打包、版本管理等流程。
  支持多平台导出和自动化构建。
version: 1.0.0
dependencies:
  - godot-core
  - file-manager
triggers:
  - pattern: "导出|打包|构建|build|export|发布|release"
inputs:
  - name: platform
    type: string
    enum: ["windows", "linux", "macos", "android", "ios", "web"]
    required: true
  - name: build_type
    type: string
    enum: ["debug", "release"]
    default: "release"
outputs:
  - name: build_output
    type: directory
    path_pattern: "builds/{platform}/"
---

# 构建流水线技能

管理 Godot 项目的导出和发布流程。

## 导出配置

### export_presets.cfg 模板

```ini
[preset.0]

name="Windows Desktop"
platform="Windows Desktop"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="builds/windows/{project_name}.exe"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=1
binary_format/embed_pck=true
texture_format/bptc=true
texture_format/s3tc=true
texture_format/etc=false
texture_format/etc2=false
codesign/enable=false
application/modify_resources=true
application/icon="res://icon.ico"
application/console_wrapper_icon=""
application/icon_interpolation=4
application/file_version=""
application/product_version=""
application/company_name=""
application/product_name=""
application/file_description=""
application/copyright=""
application/trademarks=""
application/export_angle=0
ssh_remote_deploy/enabled=false

[preset.1]

name="Linux/X11"
platform="Linux/X11"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="builds/linux/{project_name}.x86_64"

[preset.1.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=1
binary_format/embed_pck=true
texture_format/bptc=true
texture_format/s3tc=true
texture_format/etc=false
texture_format/etc2=false
ssh_remote_deploy/enabled=false

[preset.2]

name="macOS"
platform="macOS"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="builds/macos/{project_name}.dmg"

[preset.2.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=0
binary_format/architecture="universal"
application/icon="res://icon.icns"
application/icon_interpolation=4
application/bundle_identifier=""
application/signature=""
application/app_category="Games"
application/short_version=""
application/version=""
application/copyright=""
application/copyright_localized={}
application/min_macos_version="10.12"
application/export_angle=0
display/high_res=true
codesign/codesign=1
codesign/identity=""
codesign/certificate_file=""
codesign/certificate_password=""
codesign/entitlements/custom_file=""
notarization/notarization=0
ssh_remote_deploy/enabled=false

[preset.3]

name="Android"
platform="Android"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="builds/android/{project_name}.apk"

[preset.3.options]

custom_template/debug=""
custom_template/release=""
gradle_build/use_gradle_build=false
gradle_build/export_format=0
gradle_build/min_sdk=""
gradle_build/target_sdk=""
architectures/armeabi-v7a=true
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
version/code=1
version/name="1.0.0"
package/unique_name="com.example.game"
package/name=""
package/signed=true
package/app_category=2
package/retain_data_on_uninstall=false
package/exclude_from_recents=false
launcher_icons/main_192x192=""
launcher_icons/adaptive_foreground_432x432=""
launcher_icons/adaptive_background_432x432=""
graphics/opengl_debug=false
xr_features/xr_mode=0
screen/immersive_mode=true
screen/support_small=true
screen/support_normal=true
screen/support_large=true
screen/support_xlarge=true
user_data_backup/allow=false
command_line/extra_args=""
apk_expansion/enable=false
apk_expansion/SALT=""
apk_expansion/public_key=""
permissions/custom_permissions=PackedStringArray()
permissions/access_checkin_properties=false
permissions/access_coarse_location=false
permissions/access_fine_location=false
permissions/access_network_state=false
permissions/access_wifi_state=false
permissions/camera=false
permissions/change_network_state=false
permissions/change_wifi_multicast_state=false
permissions/change_wifi_state=false
permissions/internet=true
permissions/read_external_storage=false
permissions/record_audio=false
permissions/vibrate=true
permissions/write_external_storage=false

[preset.4]

name="Web"
platform="Web"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="builds/web/index.html"

[preset.4.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
progressive_web_app/offline_page=""
progressive_web_app/display=1
progressive_web_app/orientation=0
progressive_web_app/icon_144x144=""
progressive_web_app/icon_180x180=""
progressive_web_app/icon_512x512=""
progressive_web_app/background_color=Color(0, 0, 0, 1)
```

---

## 构建脚本

### build.gd (编辑器脚本)

```gdscript
@tool
## 构建脚本
##
## 在编辑器中执行自动化构建
extends EditorScript

const BUILD_DIR = "builds/"
const VERSION_FILE = "res://version.txt"

func _run() -> void:
    print("=== 开始构建 ===")
    
    var version = _read_version()
    print("版本: " + version)
    
    _clean_build_dir()
    _export_all_platforms(version)
    
    print("=== 构建完成 ===")

func _read_version() -> String:
    if FileAccess.file_exists(VERSION_FILE):
        var file = FileAccess.open(VERSION_FILE, FileAccess.READ)
        return file.get_as_text().strip_edges()
    return "1.0.0"

func _clean_build_dir() -> void:
    var dir = DirAccess.open("res://")
    if dir.dir_exists(BUILD_DIR):
        # 递归删除
        _remove_dir_recursive(BUILD_DIR)
    dir.make_dir(BUILD_DIR)

func _remove_dir_recursive(path: String) -> void:
    var dir = DirAccess.open(path)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if file_name != "." and file_name != "..":
                var full_path = path + "/" + file_name
                if dir.current_is_dir():
                    _remove_dir_recursive(full_path)
                else:
                    dir.remove(file_name)
            file_name = dir.get_next()
        dir.list_dir_end()
        DirAccess.open("res://").remove(path)

func _export_all_platforms(version: String) -> void:
    var export_presets = [
        {"name": "Windows Desktop", "suffix": ".exe"},
        {"name": "Linux/X11", "suffix": ".x86_64"},
        {"name": "Web", "suffix": ""}
    ]
    
    for preset in export_presets:
        _export_platform(preset.name, version, preset.suffix)

func _export_platform(preset_name: String, version: String, suffix: String) -> void:
    print("导出: " + preset_name)
    
    var platform_dir = BUILD_DIR + preset_name.to_lower().replace("/", "_").replace(" ", "_")
    DirAccess.open("res://").make_dir_recursive(platform_dir)
    
    # 使用 EditorExportPlatform 导出
    # 注意：这需要在编辑器中运行
```

---

## 版本管理

### version.txt

```
1.0.0
```

### version_manager.gd

```gdscript
## 版本管理器
class_name VersionManager

const VERSION_FILE = "res://version.txt"

static func get_version() -> String:
    if FileAccess.file_exists(VERSION_FILE):
        var file = FileAccess.open(VERSION_FILE, FileAccess.READ)
        return file.get_as_text().strip_edges()
    return "0.0.0"

static func set_version(version: String) -> void:
    var file = FileAccess.open(VERSION_FILE, FileAccess.WRITE)
    file.store_string(version)

static func bump_patch() -> String:
    var current = get_version()
    var parts = current.split(".")
    parts[2] = str(int(parts[2]) + 1)
    var new_version = ".".join(parts)
    set_version(new_version)
    return new_version

static func bump_minor() -> String:
    var current = get_version()
    var parts = current.split(".")
    parts[1] = str(int(parts[1]) + 1)
    parts[2] = "0"
    var new_version = ".".join(parts)
    set_version(new_version)
    return new_version

static func bump_major() -> String:
    var current = get_version()
    var parts = current.split(".")
    parts[0] = str(int(parts[0]) + 1)
    parts[1] = "0"
    parts[2] = "0"
    var new_version = ".".join(parts)
    set_version(new_version)
    return new_version
```

---

## CI/CD 配置

### GitHub Actions

#### .github/workflows/build.yml

```yaml
name: Build Game

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

env:
  GODOT_VERSION: 4.6
  PROJECT_NAME: MyGame

jobs:
  build-windows:
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.6
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup
        run: |
          mkdir -v -p ~/.local/share/godot/export_templates
          mv /root/.local/share/godot/export_templates/${GODOT_VERSION}.stable ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable
      
      - name: Build Windows
        run: |
          mkdir -v -p builds/windows
          godot --headless --export-release "Windows Desktop" builds/windows/${PROJECT_NAME}.exe
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: windows-build
          path: builds/windows

  build-linux:
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.6
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup
        run: |
          mkdir -v -p ~/.local/share/godot/export_templates
          mv /root/.local/share/godot/export_templates/${GODOT_VERSION}.stable ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable
      
      - name: Build Linux
        run: |
          mkdir -v -p builds/linux
          godot --headless --export-release "Linux/X11" builds/linux/${PROJECT_NAME}.x86_64
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: linux-build
          path: builds/linux

  build-web:
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.6
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup
        run: |
          mkdir -v -p ~/.local/share/godot/export_templates
          mv /root/.local/share/godot/export_templates/${GODOT_VERSION}.stable ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable
      
      - name: Build Web
        run: |
          mkdir -v -p builds/web
          godot --headless --export-release "Web" builds/web/index.html
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: web-build
          path: builds/web

  create-release:
    needs: [build-windows, build-linux, build-web]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        
      - name: Create ZIP archives
        run: |
          cd windows-build && zip -r ../${PROJECT_NAME}-windows.zip . && cd ..
          cd linux-build && zip -r ../${PROJECT_NAME}-linux.zip . && cd ..
          cd web-build && zip -r ../${PROJECT_NAME}-web.zip . && cd ..
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            ${PROJECT_NAME}-windows.zip
            ${PROJECT_NAME}-linux.zip
            ${PROJECT_NAME}-web.zip
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitLab CI

#### .gitlab-ci.yml

```yaml
image: barichello/godot-ci:4.6

stages:
  - build
  - deploy

variables:
  GODOT_VERSION: "4.6"
  PROJECT_NAME: "MyGame"

before_script:
  - mkdir -v -p ~/.local/share/godot/export_templates
  - mv /root/.local/share/godot/export_templates/${GODOT_VERSION}.stable ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable

build:windows:
  stage: build
  script:
    - mkdir -v -p builds/windows
    - godot --headless --export-release "Windows Desktop" builds/windows/${PROJECT_NAME}.exe
  artifacts:
    paths:
      - builds/windows

build:linux:
  stage: build
  script:
    - mkdir -v -p builds/linux
    - godot --headless --export-release "Linux/X11" builds/linux/${PROJECT_NAME}.x86_64
  artifacts:
    paths:
      - builds/linux

build:web:
  stage: build
  script:
    - mkdir -v -p builds/web
    - godot --headless --export-release "Web" builds/web/index.html
  artifacts:
    paths:
      - builds/web

pages:
  stage: deploy
  dependencies:
    - build:web
  script:
    - mv builds/web public
  artifacts:
    paths:
      - public
  only:
    - main
```

---

## 命令行构建

### 本地构建脚本

#### build.ps1 (Windows PowerShell)

```powershell
param(
    [string]$Platform = "all",
    [string]$BuildType = "release",
    [string]$GodotPath = "C:\Godot\Godot_v4.6-stable_win64.exe"
)

$ProjectName = "MyGame"
$BuildDir = "builds"

function Build-Platform {
    param([string]$PresetName, [string]$OutputDir, [string]$FileName)
    
    Write-Host "Building for $PresetName..."
    
    New-Item -ItemType Directory -Force -Path "$BuildDir/$OutputDir" | Out-Null
    
    $exportArg = if ($BuildType -eq "debug") { "--export-debug" } else { "--export-release" }
    
    & $GodotPath --headless $exportArg $PresetName "$BuildDir/$OutputDir/$FileName"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $PresetName build completed" -ForegroundColor Green
    } else {
        Write-Host "✗ $PresetName build failed" -ForegroundColor Red
    }
}

# 清理构建目录
if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
}

switch ($Platform) {
    "windows" {
        Build-Platform "Windows Desktop" "windows" "$ProjectName.exe"
    }
    "linux" {
        Build-Platform "Linux/X11" "linux" "$ProjectName.x86_64"
    }
    "web" {
        Build-Platform "Web" "web" "index.html"
    }
    "all" {
        Build-Platform "Windows Desktop" "windows" "$ProjectName.exe"
        Build-Platform "Linux/X11" "linux" "$ProjectName.x86_64"
        Build-Platform "Web" "web" "index.html"
    }
    default {
        Write-Host "Unknown platform: $Platform"
        Write-Host "Available: windows, linux, web, all"
    }
}

Write-Host "`nBuild complete!"
```

#### build.sh (Linux/macOS)

```bash
#!/bin/bash

PLATFORM=${1:-"all"}
BUILD_TYPE=${2:-"release"}
GODOT_PATH=${GODOT_PATH:-"godot"}
PROJECT_NAME="MyGame"
BUILD_DIR="builds"

build_platform() {
    local preset=$1
    local output_dir=$2
    local filename=$3
    
    echo "Building for $preset..."
    
    mkdir -p "$BUILD_DIR/$output_dir"
    
    if [ "$BUILD_TYPE" = "debug" ]; then
        export_arg="--export-debug"
    else
        export_arg="--export-release"
    fi
    
    $GODOT_PATH --headless $export_arg "$preset" "$BUILD_DIR/$output_dir/$filename"
    
    if [ $? -eq 0 ]; then
        echo "✓ $preset build completed"
    else
        echo "✗ $preset build failed"
    fi
}

# 清理
rm -rf "$BUILD_DIR"

case $PLATFORM in
    "windows")
        build_platform "Windows Desktop" "windows" "$PROJECT_NAME.exe"
        ;;
    "linux")
        build_platform "Linux/X11" "linux" "$PROJECT_NAME.x86_64"
        ;;
    "macos")
        build_platform "macOS" "macos" "$PROJECT_NAME.dmg"
        ;;
    "web")
        build_platform "Web" "web" "index.html"
        ;;
    "all")
        build_platform "Windows Desktop" "windows" "$PROJECT_NAME.exe"
        build_platform "Linux/X11" "linux" "$PROJECT_NAME.x86_64"
        build_platform "Web" "web" "index.html"
        ;;
    *)
        echo "Unknown platform: $PLATFORM"
        echo "Available: windows, linux, macos, web, all"
        ;;
esac

echo ""
echo "Build complete!"
```

---

## 发布清单

### 发布前检查

```markdown
## 发布清单

### 代码质量
- [ ] 所有功能测试通过
- [ ] 无控制台错误/警告
- [ ] 移除所有调试代码
- [ ] 移除测试场景

### 性能
- [ ] 目标平台帧率达标
- [ ] 内存使用合理
- [ ] 加载时间可接受

### 资源
- [ ] 所有资源已优化
- [ ] 纹理压缩正确
- [ ] 音频格式正确

### 配置
- [ ] 版本号已更新
- [ ] 导出设置正确
- [ ] 应用图标已设置

### 平台特定
- [ ] Windows: 图标/签名
- [ ] macOS: 签名/公证
- [ ] Android: 签名/权限
- [ ] Web: 兼容性测试

### 发布
- [ ] 更新日志已写
- [ ] README 已更新
- [ ] 创建 Git Tag
```

---

## 使用示例

```
构建并导出游戏：
- 平台：Windows + Web
- 版本：自动递增补丁版本
- 上传到 GitHub Release
```
