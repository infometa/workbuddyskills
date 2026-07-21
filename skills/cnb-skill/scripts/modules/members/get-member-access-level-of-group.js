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
 * @Source /{group}/-/members/access-level
 */

/**
 * @description getMemberAccessLevelOfGroup request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetMemberAccessLevelOfGroupRes Success Response Type
 */

/**
 * @description GetMemberAccessLevelOfGroupError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:r
* @tags Members
* @name getMemberAccessLevelOfGroup
* @summary 获取指定组织内, 访问成员在当前层级内的权限信息。Get permission information for accessing members at current level.
* @request get:/{group}/-/members/access-level

----------------------------------
* @param {GetMemberAccessLevelOfGroupParams} arg0 - getMemberAccessLevelOfGroup request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  group,
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
    url: `/${group}/-/members/access-level`,
    _apiTag: "/{group}/-/members/access-level",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{group}/-/members/access-level",
      path: {
        group
      },
      query: query
    }
  });
}