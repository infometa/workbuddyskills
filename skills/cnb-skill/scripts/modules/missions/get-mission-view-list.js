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
 * @Source /{mission}/-/mission/view-list
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetMissionViewListRes Success Response Type
 */

/**
 * @description GetMissionViewListError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* mission-manage:r
* @tags Missions
* @name getMissionViewList
* @summary 获取任务集视图列表。Get view list of a mission.
* @request get:/{mission}/-/mission/view-list

----------------------------------
* @param {string} arg0
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default(mission, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${mission}/-/mission/view-list`,
    _apiTag: "/{mission}/-/mission/view-list",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{mission}/-/mission/view-list",
      path: {
        mission
      }
    }
  });
}