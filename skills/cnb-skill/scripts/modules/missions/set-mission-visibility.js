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
 * @Source /{mission}/-/settings/set_visibility
 */

/**
 * @description setMissionVisibility request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description SetMissionVisibilityRes Success Response Type
 */

/**
 * @description SetMissionVisibilityError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* mission-manage:rw
* @tags Missions
* @name setMissionVisibility
* @summary 改变任务集可见性。Update the visibility of a mission.
* @request post:/{mission}/-/settings/set_visibility

----------------------------------
* @param {SetMissionVisibilityParams} arg0 - setMissionVisibility request params
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
    url: `/${mission}/-/settings/set_visibility`,
    _apiTag: "/{mission}/-/settings/set_visibility",
    method: "post",
    params: query,
    _originParams: {
      method: "post",
      _apiTag: "/{mission}/-/settings/set_visibility",
      path: {
        mission
      },
      query: query
    }
  });
}