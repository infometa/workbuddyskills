# Mode E — RESTful Call

> **Terminology**: 模板 = template | 产物 = deliverable/output | 同构版本 = isomorphic version (same logic, different language) | endpoint = API endpoint URL | 鉴权规则 = authentication rules | Edit 写文件 = Edit to write file (insert mode)

## Template Selection
By appType → language:
- node-server → `src/lib/te-track.ts` (axios)
- python-server → `src/lib/te_track.py` (requests)
- go-server → `src/lib/te_track.go` (net/http)
- java-server → `src/main/java/.../TeTrack.java` (OkHttp)

## Deliverable (Node example)
```ts
// src/lib/te-track.ts
import axios from 'axios';

const SERVER_URL = '<SERVER_URL>';
const APPID = '<appId>';

export async function track(event: string, props: Record<string, unknown>, distinctId: string) {
  await axios.post(`${SERVER_URL}/sync_json`, {
    appid: APPID,
    event,
    '#time': new Date().toISOString(),
    '#distinct_id': distinctId,
    properties: { ...props },
  }, { headers: { 'Content-Type': 'application/json' } });
}
```

Other languages: provide isomorphic versions. Reference `~/.ae-cli/wiki/synthesis/restful-api-reference.md`.

## Generation Steps
1. Select template by appType; confirm endpoint/auth rules from wiki
2. If CWD is a server project → directly Edit to write file (simplified version of Mode A Stage 3 logic)
3. Otherwise → deliver as snippet per Mode B
