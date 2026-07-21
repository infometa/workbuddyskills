# 完整示例

## 示例 1：上传图片并获取公共链接

```bash
API_HOST="https://lxapi.lexiangla.com"
TOKEN="lxmcp_your_token_here"

# 上传图片
RESULT=$(curl -s -X POST "${API_HOST}/cgi-bin/v1/assets" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "type=image" \
  -F "file=@/path/to/photo.jpg" \
  -F "is_public=1")

echo "上传结果:"
echo $RESULT | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))"
```

## 示例 2：批量上传图片

```bash
API_HOST="https://lxapi.lexiangla.com"
TOKEN="lxmcp_your_token_here"

for img in *.jpg *.png; do
  [ -f "$img" ] || continue
  echo "上传: $img"
  curl -s -X POST "${API_HOST}/cgi-bin/v1/assets" \
    -H "Authorization: Bearer ${TOKEN}" \
    -F "type=image" \
    -F "file=@${img}" \
    -F "is_public=1"
  echo ""
done
```

## 示例 3：下载图片资源

```bash
ASSET_ID="68975160a41211ebbcc38ead0db1c463"

RESULT=$(curl -s -X GET "${API_HOST}/cgi-bin/v1/assets/${ASSET_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

DOWNLOAD_URL=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")
MIME_TYPE=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('mime_type', 'unknown'))")

echo "MIME: ${MIME_TYPE}"
curl -s -o "downloaded_image.jpg" "${DOWNLOAD_URL}"
echo "✅ 已下载"
```
