#!/usr/bin/env node

/**
 * 同程程心数据工具库
 *
 * 提供统一的数据解包和安全访问方法
 */

/**
 * 统一的数据解包方法
 * 
 * 从 API 响应中提取业务数据 (res.data)
 * 
 * @param {object} res - API 响应对象
 * @returns {object|null} 解包后的业务数据，如果无法解包则返回 null
 */
function extract_response_data(res) {
  if (res && res.data !== undefined) {
    return res.data;
  }
  
  // 无法解包
  return null;
}

/**
 * 安全获取列表数据
 * 
 * 从解包后的数据中安全提取指定键名的列表
 * 如果数据不存在或不是数组，返回空数组
 * 
 * @param {object} data - 解包后的业务数据
 * @param {string} key - 列表键名（如 'trainDataList', 'hotelDataList'）
 * @returns {Array} 列表数据，如果不存在则返回空数组
 */
function get_list_data(data, key) {
  if (!data || !key) {
    return [];
  }
  
  const list = data[key];
  return Array.isArray(list) ? list : [];
}

/**
 * 判断是否为中转联程
 * 
 * 检查行程数据是否为中转联程类型（tripType === 'TRANSFER'）
 * 并且包含有效的分段行程列表（segmentList 存在且长度大于 0）
 * 
 * @param {object} item - 行程数据对象
 * @param {string} item.tripType - 行程类型（如 'TRANSFER', 'DIRECT'）
 * @param {Array} item.segmentList - 分段行程列表
 * @returns {boolean} 是否为中转联程
 */
function is_transfer_trip(item) {
  return item.tripType === 'TRANSFER' && 
         item.segmentList && 
         item.segmentList.length > 0;
}

/**
 * 判断是否为往返行程
 * 
 * 检查 extra 参数中是否包含"往返"字样
 * 
 * @param {string} extra - 额外信息参数
 * @returns {boolean} 是否为往返行程
 */
function is_round_trip(extra) {
  return typeof extra === 'string' && extra.includes('往返');
}

module.exports = {
  extract_response_data,
  get_list_data,
  is_transfer_trip,
  is_round_trip
};
