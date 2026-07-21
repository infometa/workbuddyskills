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
 * @Source /{repo}/-/members/access-level
 */

/**
 * @description getMemberAccessLevelOfRepo request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetMemberAccessLevelOfRepoRes Success Response Type
 */

/**
 * @description GetMemberAccessLevelOfRepoError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags Members
* @name getMemberAccessLevelOfRepo
* @summary 获取指定仓库内, 访问成员在当前层级内的权限信息。Get permission information for accessing members at current level.
* @request get:/{repo}/-/members/access-level

----------------------------------
* @param {GetMemberAccessLevelOfRepoParams} arg0 - getMemberAccessLevelOfRepo request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
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
    url: `/${repo}/-/members/access-level`,
    _apiTag: "/{repo}/-/members/access-level",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/members/access-level",
      path: {
        repo
      },
      query: query
    }
  });
}