// scripts/lib/reg-room.js
// Leaf module (no internal imports) holding the self-contained enter-room
// regex parser. Shared by roominfo.js and tpl-func.js to avoid an import
// cycle (timeline -> tpl-func -> roominfo -> timeline).
// Pure-JS port of the browser SDK log-utils getEnterRoomParasmFromLog.
// Node built-ins only, no npm imports.

const keywords = [
  'user_id',
  'room_id',
  'str_room_id',
  'role',
  'stream_id',
  'user_define_record_id',
  'scene',
  'mode',
  'business_info',
  'self',
];

function filterDirtyMatch(ret) {
  if (keywords.some(item => item.includes(ret))) {
    return '';
  }
  return ret;
}

// 进房参数提取
export function getEnterRoomParasmFromLog(log) {
  // 优化性能，先 test 命中了再 exec
  const isMatch = /trtc(_|-)api.*enterRoom/i.test(log);
  if (!isMatch) {
    return undefined;
  }
  // 各个版本各个终端的 sdk 日志打印的五花八门，逐个变量匹配
  const { sdkAppId } = /sdkAppId:\s*(?<sdkAppId>[0-9]+)/i.exec(log)?.groups || {};
  if (!sdkAppId) {
    return undefined;
  }
  const { userId = '' } = /(user_id|userId):\s*(?<userId>[0-9a-zA-Z-_]+)/i.exec(log)?.groups || {};
  const { roomId = '' } = /(room_id|roomId):\s*(?<roomId>[0-9]+)/i.exec(log)?.groups || {};
  const { strRoomId = '' } = /(str_room_id|strRoomId):\s*(?<strRoomId>[a-zA-Z0-9!#$%&()+\-_]+)/i.exec(log)?.groups || {};
  const { role = '' } = /role:\s*(?<role>[a-zA-Z]+)/i.exec(log)?.groups || {};
  const { streamId = '' } = /(stream_id|streamId):\s*(?<streamId>\w+)/i.exec(log)?.groups || {};
  const { userDefineRecordId = '' } = /(user_define_record_id|userDefineRecordId):\s*(?<userDefineRecordId>\w+)/i.exec(log)?.groups || {};
  const { scene = '' } = /(scene|mode):\s*(?<scene>[a-zA-Z]+)/i.exec(log)?.groups || {};
  return {
    sdkAppId,
    userId,
    roomId: roomId === '0' ? '' : filterDirtyMatch(roomId),
    strRoomId: filterDirtyMatch(strRoomId),
    role: filterDirtyMatch(role),
    streamId: filterDirtyMatch(streamId),
    userDefineRecordId: filterDirtyMatch(userDefineRecordId),
    scene: filterDirtyMatch(scene),
  };
}
