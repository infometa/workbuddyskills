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
 * @description Other reuqest params
 */

/**
 * @description PostMissionViewConfigRes Success Response Type
 */

/**
 * @description PostMissionViewConfigError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* mission-manage:rw
* @tags Missions
* @name postMissionViewConfig
* @summary 设置任务集视图配置信息。Set mission view config.
* @request post:/{mission}/-/mission/view

----------------------------------
* @param {string} arg0
* @param {DtoMissionViewConfig} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(mission, request, {
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
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{mission}/-/mission/view",
      path: {
        mission
      },
      body: request
    }
  });
}