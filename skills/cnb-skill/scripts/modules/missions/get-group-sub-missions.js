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
 * @Source /{slug}/-/missions
 */

/**
 * @description getGroupSubMissions request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetGroupSubMissionsRes Success Response Type
 */

/**
 * @description GetGroupSubMissionsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-resource:r
* @tags Missions
* @name getGroupSubMissions
* @summary 查询组织下面用户有权限查看到的任务集。Query all missions that the user has permission to see under the specific organization.
* @request get:/{slug}/-/missions

----------------------------------
* @param {GetGroupSubMissionsParams} arg0 - getGroupSubMissions request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
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
    url: `/${slug}/-/missions`,
    _apiTag: "/{slug}/-/missions",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/missions",
      path: {
        slug
      },
      query: query
    }
  });
}