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
 * @Source /{mission}
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteMissionRes Success Response Type
 */

/**
 * @description DeleteMissionError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* mission-delete:rw
* @tags Missions
* @name deleteMission
* @summary 删除指定任务集。Delete the specified mission.
* @request delete:/{mission}

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
    url: `/${mission}`,
    _apiTag: "/{mission}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{mission}",
      path: {
        mission
      }
    }
  });
}