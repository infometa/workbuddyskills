"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = _default;
var _core = _interopRequireDefault(require("../../core/core.js"));
function _interopRequireDefault(e) { return e && e.__esModule ? e : { default: e }; }
// @ts-nocheck
/* tslint:disable */
/* eslint-disable */
/*
 * -------------------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA CNB-API-GENERATE                        ##
 * ##                                                                     ##
 * ## AUTHOR: bapelin                                                     ##
 * ## SOURCE: https://cnb.woa.com/cnb/frontend-science/cnb-api-generate   ##
 * -------------------------------------------------------------------------
 * @Version 2.2.5
 * @Source /{mission}/-/mission/view
 */

/**
 * @description getMissionViewConfig request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetMissionViewConfigRes Success Response Type
 */

/**
 * @description GetMissionViewConfigError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* mission-manage:r
* @tags Missions
* @name getMissionViewConfig
* @summary 查询任务集视图配置信息。Get mission view config.
* @request get:/{mission}/-/mission/view

----------------------------------
* @param {GetMissionViewConfigParams} arg0 - getMissionViewConfig request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  mission,
  ...query
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${mission}/-/mission/view`,
    _apiTag: "/{mission}/-/mission/view",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{mission}/-/mission/view",
      path: {
        mission
      },
      query: query
    }
  });
}