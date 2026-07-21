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
 * @Source /user/groups
 */

/**
 * @description listTopGroups request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListTopGroupsRes Success Response Type
 */

/**
 * @description ListTopGroupsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Organizations
* @name listTopGroups
* @summary 获取当前用户拥有权限的顶层组织列表。Get top-level organizations list that the current user has access to.
* @request get:/user/groups

----------------------------------
* @param {ListTopGroupsParams} arg0 - listTopGroups request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
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
    url: "/user/groups",
    _apiTag: "/user/groups",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/user/groups",
      query: query
    }
  });
}