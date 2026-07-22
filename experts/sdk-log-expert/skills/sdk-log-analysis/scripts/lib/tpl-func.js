// scripts/lib/tpl-func.js
// Pure-JS port of the browser SDK log-utils art-template filter set.
// Node built-ins only, no npm imports, no dayjs.
//
// i18n note: the browser wraps Chinese in t('中文') / t('模板 {{x}}', {x}).
// The skill has no i18n runtime, so plain t('中文') is inlined as the literal
// '中文', and parameterized strings are built with template literals.
//
// Canonical home for template-filter helpers. timeline.js imports getTplPlugins
// from here. The 7 pre-existing filters keep their exact prior behavior so the
// regression tests (e.g. 错误码-3319, sdkAppId : 1400460191) stay identical.

import { getEnterRoomParasmFromLog } from './reg-room.js';

// ---------------------------------------------------------------------------
// userState filter (parseUserListBefore95 / parseUserList / userState)
// ---------------------------------------------------------------------------

const parseUserListBefore95 = (stateListStr) => {
  const list = stateListStr.split(']').filter(Boolean);
  return list.reduce((arr, userStateStr) => {
    const { userId } = /\[(?<userId>\w+)\|.*/.exec(userStateStr)?.groups || {};
    if (userId) {
      return arr.concat([`userId: ${userId}`]);
    }
    return arr;
  }, []);
};

const parseUserList = (stateListStr, withState = true) => {
  if (/\[\w+\|\w+\|.*\]/.test(stateListStr)) {
    return parseUserListBefore95(stateListStr);
  }

  const list = stateListStr.split('}').filter(Boolean);
  return list.reduce((arr, userStateStr) => {
    const { userId } = /uid:\s*(?<userId>\w+)/.exec(userStateStr)?.groups || {};
    if (userId) {
      const { audioState } = /\[Audio:\s*(?<audioState>[a-zA-Z+]+)\]/.exec(userStateStr)?.groups || {};
      let audioStr;
      switch (audioState) {
        case 'Has':
          audioStr = '有';
          break;
        case 'Mute':
          audioStr = 'Mute';
          break;
        case undefined:
          audioStr = '无';
          break;
        default:
          audioStr = audioState;
          break;
      }
      const { videoState } = /\[Video:\s*(?<videoState>[a-zA-Z+]+)\]/.exec(userStateStr)?.groups || {};
      let videoStr;
      switch (videoState) {
        case 'Big':
          videoStr = '主流';
          break;
        case 'Aux':
          videoStr = '辅流（屏幕分享）';
          break;
        case 'Big+Small':
          videoStr = '大流+小流';
          break;
        case 'Big+Small+Aux':
          videoStr = '大流+小流+辅流（屏幕分享）';
          break;
        case undefined:
          videoStr = '无';
          break;
        default:
          videoStr = videoState;
          break;
      }
      return arr.concat(withState
        ? [`userId: ${userId}, 音频: ${audioStr}, 视频: ${videoStr}`]
        : [`userId: ${userId}`]);
    }
    return arr;
  }, []);
};

export const userState = (log) => {
  if (log.indexOf('Enter UserList') !== -1) {
    const listStr = log.split('Enter UserList:')[1];
    const userList = parseUserList(listStr);
    return `用户进房: ${userList.join(';')}`;
  }
  if (log.indexOf('Exit UserList') !== -1) {
    const listStr = log.split('Exit UserList:')[1];
    const userList = parseUserList(listStr, false);
    return `用户退房: ${userList.join(';')}`;
  }
  if (log.indexOf('StateChange') !== -1) {
    const listStr = log.split('UserList:')[1];
    if (listStr.indexOf('to:') === -1) {
      return `用户状态更新: ${parseUserListBefore95(listStr)}`;
    }
    const changeList = listStr.split('to:');
    const preList = parseUserList(changeList[0]);
    const nextList = parseUserList(changeList[1]);
    return `用户状态更新: 【${preList.join(';')}】新状态:【${nextList.join(';')}】`;
  }
  return '';
};

// ---------------------------------------------------------------------------
// JSON / key-path / 3A / key-value helpers
// (moved from timeline.js verbatim — behavior must stay identical for the
//  existing 7 filters guarded by regression tests).
// ---------------------------------------------------------------------------

export function getJSONKeyPath(target, keypath) {
  return String(keypath || '').split('.').reduce((previous, current) => {
    if (previous == null) return null;
    if (Array.isArray(previous) && Number.isNaN(Number(current))) return previous[0]?.[current];
    return previous[current];
  }, target);
}

export function extractJsonFromLog(log) {
  const result = [];
  const text = String(log || '');
  for (let i = 0; i < text.length; i++) {
    if (text[i] !== '{') continue;
    let depth = 0;
    let inString = false;
    let escaped = false;
    for (let j = i; j < text.length; j++) {
      const ch = text[j];
      if (inString) {
        if (escaped) escaped = false;
        else if (ch === '\\') escaped = true;
        else if (ch === '"') inString = false;
        continue;
      }
      if (ch === '"') inString = true;
      else if (ch === '{') depth++;
      else if (ch === '}') {
        depth--;
        if (depth === 0) {
          try { result.push(JSON.parse(text.slice(i, j + 1))); } catch {}
          i = j;
          break;
        }
      }
    }
  }
  return result;
}

export function parseKeyValuePair(log, key) {
  if (key) {
    const re = new RegExp(`${key}\\s*(:|=)\\s*(?<value>[.a-zA-Z0-9_-]+)`, 'i');
    return re.exec(log)?.groups?.value || '';
  }
  return '';
}

export function parseAudio3AConfig(log) {
  const result = { aecOn: false, ansOn: false, ainsOn: false, agcOn: false };
  for (const match of String(log || '').matchAll(/k(?:Aec|Ans|Agc)(?:Level_)?_?(\d+)/gi)) {
    const name = match[0].toLowerCase();
    const value = Number(match[1]);
    if (name.startsWith('kaec') && !result.aec) result.aec = value;
    if (name.startsWith('kans') && !result.ans) result.ans = value;
    if (name.startsWith('kagc') && !result.agc) result.agc = value;
  }
  result.aecOn = Boolean(result.aec);
  result.ansOn = Boolean(result.ans);
  result.agcOn = Boolean(result.agc);
  result.ainsOn = result.ans === 120;
  return result;
}

// ---------------------------------------------------------------------------
// enum / api lookup tables (t('中文') -> '中文')
// ---------------------------------------------------------------------------

const enumMap = {
  kSpeakerPhone: () => '扬声器',
  kEarPhone: () => '听筒播放（手机顶部接听电话位置）',
  kWiredHeadSet: () => '有线耳机或者声卡等外设',
  kBluetoothHeadSet: () => '蓝牙耳机',
};

const apiMap = {
  setSEIPayloadType: () => '设置SEI',
  enableAudioAEC: () => '音频AEC开关',
  enableAudioAGC: () => '音频AGC开关',
  enableAudioANS: () => '开关ANS',
  enableFillCoverRegion: () => '启用屏幕分享被遮挡区域隐藏特性',
  enableAdvancedScreenCapture: () => '启用屏幕采集抗遮挡特性',
  setSubStreamEncoderParam: () => '设置辅流编码参数',
  sendJsonCMD: () => '客户调用server定制逻辑通用接口',
  setCustomRenderMode: () => '设置自定义渲染模式',
  setVideoEncodeParamEx: () => '设置编码参数',
  setLocalAudioMuteMode: () => '设置本地静音模式',
  muteRemoteAudioInSpeaker: () => '远程音频在扬声器中静音',
  setAudioSampleRate: () => '支持设置音频采样率（目前只用于16k）',
  setPerformanceMode: () => '设置性能模式',
  setNetEnv: () => '设置TRTC环境',
  forceCallbackMixedPlayAudioFrame: () => '强制回调MixedPlayAudioFrame',
  updatePrivateMapKey: () => '更新',
  setEncodedDataProcessingListener: () => '设置自定义加密回调',
  enableBlackStream: () => '纯音频添加黑帧',
  exitRoomWhenTerminate: () => '杀进程执行退房逻辑',
  enableSystemLoopbackAudioAEC: () => '开关系统混音AEC和设置级别',
  setFramework: () => '设置框架',
  enablePopupTips: () => '是否打开权限提示弹窗',
  setWindowCaptureStrategy: () => '设置窗口采集策略',
  disableScreenCaptureDXGI: () => '是否禁用',
  checkDuplicateEnterRoom: () => '是否检查重复调用进房',
  setScreenCaptureCropRect: () => '设定',
  setAudioQualityEx: () => '设定音质参数',
  setScreenCaptureScaleMode: () => '设置屏幕采集缩放模式(高性能/高清晰)',
  setAudioDeviceSwitchStrategy: () => '设置音频设备切换策略',
  setAudioPacketExtraDataListener: () => '设置网络层音频包回调',
  muteDuringAECWarmUp: () => '启用AEC对收敛过程中的语音静音逻辑（目前1s）',
  setLocalAudioMuteAction: () => 'mute',
  setReverbParam: () => '混响自定义参数设置',
  preloadMusic: () => '预加载bgm',
  SetAudioCacheParams: () => '设置音频Jitter本地cache大小',
  setExposureTargetBias: () => '曝光值设置',
  setCaptureResolution: () => '设置采集分辨率',
  setMediaCodecConfig: () => '自定义编解码参数透传',
  reportOnlineLog: () => '上报在线日志',
  setRoomType: () => '设置房间的类型（V2进房）',
  setAudioCacheType: () => '用于设置低延时观看还是普通延时观看',
  addCustomMonitorEvent: () => '自定义event上报',
  enableHowlingDetect: () => '开启啸叫检测',
  setCustom3aImplement: () => '设置自定义3A处理库',
  setEqualizationParam: () => '设置均衡器参数',
  disconnectOtherRoom: () => '结束跨房连麦',
  enableHevcEncode: () => '开启265编码',
  cameraPreviewOrientation: () => '固定采集画面朝向',
  keepCameraPreviewOrientation: () => '',
  setHeartBeatTimeoutSec: () => '设置心跳超时时间',
  setKeepAVCaptureOption: () => '进房失败后不关闭音视频采集',
  setAVSyncPlaySources: () => '播放端双设备对齐pts播放',
  disableAutoCleanupMuteImage: () => '开启"不开摄像头推送垫片流"',
  enableRealtimeChorus: () => '开启合唱低延迟模式',
  setQoSStrategy: () => '调整QoS策略',
  setSystemAudioKitEnabled: () => '启用AudioKit',
  setCustomCaptureGLSyncMode: () => '设置自定义采集场景下预处理模式',
  GetVideoEncoderList: () => '获取本机硬编码器列表',
  setCurrentEnvironment: () => '设置electron环境',
  disableVideoHardwareDecoding: () => '禁用视频硬解',
  disableVideoHardwareRendering: () => '禁用硬件渲染加速',
  setLogUploadMode: () => '设置日志上传模式',
  setQosAppScene: () => '设置QoS场景',
  updateROIConfig: () => '启用ROI并设置参数',
  setDecoderStrategy: () => '设置解码策略',
  enableBackgroundDecoding: () => '开启后台解码',
  enableChorus: () => '开启合唱功能',
  setStereoCaptureStrategy: () => '设置双声道采集',
  setScreenCaptureAutoRotateEnabled: () => '开启屏幕录制中自动旋转',
  setPreferLocalIPStack: () => '设置ip栈',
  setLowLatencyModeEnabled: () => '设置低延时模式',
  keepCapturingAfterExiting: () => '设置退房后是否释放资源',
  enableBluetoothA2DP: () => '控制蓝牙A2DP模式',
  enableAIDenoise: () => '控制AI降噪开关',
  setGSensorMode: () => '设置重力感应模式',
  set3DSpatialAttenuationCurve: () => '设置3D衰减曲线比率',
  setMixStreamSeiMode: () => '设置混流SEI是否透传上行SEI',
  setMixExternalAudioDelay: () => '设置外部混音延迟',
  setViewBackgroundColor: () => '设置渲染控件底色',
  enableHowlingSuppression: () => '控制啸叫抑制',
  setFixedTransportProtocol: () => '强制使用udp/tcp进房',
  TuikitLog: () => '输出Tuikit日志',
  setAudioDeviceCaptureParams: () => '设置不同API的采样率',
  setBgmPublishDelay: () => '设置BGM延迟',
  setCameraAPIType: () => '设置摄像头',
};

// ---------------------------------------------------------------------------
// Full plugin map — every key the browser getPlugins returns.
// ---------------------------------------------------------------------------

export function getTplPlugins(errorCodeList) {
  const errorCode = (code) => {
    const key = String(code ?? '');
    const item = (errorCodeList || []).find(it => it.code === key || it.msg === key);
    return item?.desc || key;
  };

  return {
    __userState: userState,
    userState,
    __json: (log, attr) => {
      const json = extractJsonFromLog(log);
      return attr ? getJSONKeyPath(json, attr) : json;
    },
    __keyPath: getJSONKeyPath,
    __errorCode: errorCode,
    errorCode,
    __3a: parseAudio3AConfig,
    __enterRoom: getEnterRoomParasmFromLog,
    __valueOfKey: parseKeyValuePair,
    __enum(key) {
      if (!key) {
        return '';
      }
      const lowerKey = key.trim().toLowerCase();
      const exists = Object.keys(enumMap).find(k => k.toLowerCase() === lowerKey);
      return exists ? enumMap[exists]() : key;
    },
    __expApi(key) {
      if (!key) {
        return '';
      }
      const lowerKey = key.trim().toLowerCase();
      const exists = Object.keys(apiMap).find(k => k.toLowerCase() === lowerKey);
      return exists ? `${key}(${apiMap[exists]()})` : key;
    },
    // 时间过滤器：__date(ms) 返回 Date；__dateFormat(date, fmt) 按 yyyy-MM-dd HH:mm:ss 模式格式化。
    __date: (ms) => {
      const d = new Date(Number(ms) || 0);
      return Number.isNaN(d.getTime()) ? new Date(0) : d;
    },
    __dateFormat: (date, fmt) => {
      const d = date instanceof Date ? date : new Date(Number(date) || 0);
      if (Number.isNaN(d.getTime())) return '';
      const pad = (n, len = 2) => String(n).padStart(len, '0');
      const map = {
        yyyy: d.getFullYear(),
        MM: pad(d.getMonth() + 1),
        dd: pad(d.getDate()),
        HH: pad(d.getHours()),
        mm: pad(d.getMinutes()),
        ss: pad(d.getSeconds()),
        SSS: pad(d.getMilliseconds(), 3),
      };
      return String(fmt || 'yyyy-MM-dd HH:mm:ss').replace(
        /yyyy|MM|dd|HH|mm|ss|SSS/g,
        token => map[token],
      );
    },
  };
}
