// scripts/lib/roominfo.js
// Pure-JS port of the browser SDK log-utils room-info logic:
//   - getEnterRoomParasmFromLog / getRoomStatusLog / getSdkInfo (reg helpers)
//   - the onRoomInfo main loop
// Time handling reuses parseLogLine() from timeline.js (timeText -> *TimeFormatted, timestamp -> *Ts).
// Node built-ins only, no npm imports.

import { parseLogLine } from './timeline.js';
import { getEnterRoomParasmFromLog } from './reg-room.js';

// Re-export for backward compatibility (the function now lives in the leaf
// module reg-room.js, shared with tpl-func.js to avoid an import cycle).
export { getEnterRoomParasmFromLog };

// 匹配进房状态的日志
export function getRoomStatusLog(log) {
  const isMatch = /trtc(_|-)api.*(OnJoinRoom|OnEnterRoom)/i.test(log);
  if (!isMatch) {
    return undefined;
  }
  const { statusCode = '' } = /(code|err):(?<statusCode>-?[0-9]+)/i.exec(log)?.groups || {};
  const { elapsedTime = '' } = /(elapsed_time_ms|spendTime|cost_time):\s*(?<elapsedTime>[0-9]+)/i.exec(log)?.groups || {};

  return {
    code: parseInt(statusCode, 10),
    elapsedTime: parseInt(elapsedTime, 10),
    log,
  };
}

// 匹配 SDK 信息 banner（trtc_api = ...）
export function getSdkInfo(log) {
  if (!log.includes('trtc_api =')) {
    return undefined;
  }
  const infoMatch = /=+\s+(?<infoStr>.*)\s+=+/.exec(log); // infoStr
  if (!infoMatch?.groups?.infoStr) {
    return undefined;
  }
  const { infoStr } = infoMatch.groups;
  const match = /SDK\s+Version:\s*(?<version>[0-9.]+)/.exec(infoStr); // SDK Version
  if (!match) {
    return undefined;
  }
  return {
    infoStr,
    sdkVersion: match.groups.version,
  };
}

// 取一行日志的时间（复用 timeline.js 的 parseLogLine）
// timeText  -> *TimeFormatted
// timestamp -> *Ts
function getLineTime(logText) {
  const { timeText, timestamp } = parseLogLine(logText);
  return {
    formatted: timeText || undefined,
    timestamp: typeof timestamp === 'number' ? timestamp : undefined,
  };
}

/**
 * 从解码后的日志行中提取进房（enterRoom）信息。
 * @param {string[]} lines 原始解码后的日志行数组
 * @param {object} [options] 预留参数（当前未使用）
 * @returns {{ rooms: object[], info: object }}
 */
export function buildRoomInfo(lines, options = {}) {
  const logs = Array.isArray(lines) ? lines : [];
  let rooms = [];
  const info = {};
  let infoFound = false;
  let lastLog;
  let lastLine = 1;
  let roomStartLine = 1;

  // 日志结尾可能是空行，判断退房的逻辑
  const checkLastLog = (logText, preRoom) => {
    const endDate = getLineTime(logText || lastLog || '');
    info.endTs = endDate.timestamp;
    info.endTimeFormatted = endDate.formatted;
    // 以日志结尾的时间作为最后一次退房时间
    if (preRoom && !preRoom.endTs) {
      preRoom.endTs = endDate.timestamp;
      preRoom.endTimeFormatted = endDate.formatted;
    }
  };

  const checkInfo = (logText) => {
    if (!info.startTs) {
      const startDate = getLineTime(logText);
      info.startTs = startDate.timestamp;
      info.startTimeFormatted = startDate.formatted;
    }

    if (!infoFound) {
      const infoRet = getSdkInfo(logText); // 匹配 SDK 信息
      if (infoRet) {
        infoFound = true;
        info.infoStr = infoRet.infoStr;
        info.sdkVersion = infoRet.sdkVersion;
        return true;
      }
    }
    return false;
  };

  // 解析日志
  logs.forEach((logText, index) => {
    // 是否存在上一个房间
    const preRoom = rooms.length > 0 ? rooms[rooms.length - 1] : undefined;
    // 日志结尾可能是空行，判断退房的逻辑
    if (index === logs.length - 1) {
      checkLastLog(logText, preRoom);
    }
    if (!logText) {
      return;
    }
    lastLine = index + 1;
    lastLog = logText;

    if (checkInfo(logText)) {
      return;
    }

    // 判断当前是否是退房
    if (preRoom && !preRoom.endTs) {
      const exitRoomMatch = /\[I\]\[(?<exitDate>[0-9:.+-/\s]+)\].*onExitRoom.*/i.exec(logText);
      if (exitRoomMatch?.groups?.exitDate) { // 本次是退房
        const exitDateRet = getLineTime(logText);
        preRoom.endTs = exitDateRet.timestamp;
        preRoom.endTimeFormatted = exitDateRet.formatted;
        roomStartLine = index + 1;
        return;
      }
    }

    const room = getEnterRoomParasmFromLog(logText); // 进房参数获取

    if (room) { // 进房参数获取成功后处理参数
      const enterRoomDateRet = getLineTime(logText);
      rooms.push({ // 房间列表的展示
        ...room,
        startLine: roomStartLine,
        line: index + 1,
        logText,
        startTimeFormatted: enterRoomDateRet.formatted,
        startTs: enterRoomDateRet.timestamp,
      });
      // 本次是进房，就设置本次为上次进房的退房时间（粗略估算）
      if (preRoom && !preRoom.endTs) {
        preRoom.endTimeFormatted = enterRoomDateRet.formatted;
        preRoom.endTs = enterRoomDateRet.timestamp;
      }
    }

    const roomStatus = getRoomStatusLog(logText);
    if (roomStatus && rooms.length !== 0) {
      rooms[rooms.length - 1].roomStatus = roomStatus;
    }
  });

  // 补齐房间结束行号，用于按房间巡检
  rooms = rooms.map((room, index) => {
    const nextRoom = rooms[index + 1];
    return {
      ...room,
      endLine: nextRoom ? nextRoom.line - 1 : lastLine,
    };
  });

  return { rooms, info };
}
