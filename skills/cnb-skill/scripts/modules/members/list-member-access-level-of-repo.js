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
 * @Source /{repo}/-/members/{username}/access-level
 */

/**
 * @description listMemberAccessLevelOfRepo request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListMemberAccessLevelOfRepoRes Success Response Type
 */

/**
 * @description ListMemberAccessLevelOfRepoError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags Members
* @name listMemberAccessLevelOfRepo
* @summary 获取指定仓库内指定成员的权限信息, 结果按组织层级来展示, 包含上层组织的权限继承信息。Get specified member's permissions with organizational hierarchy.
* @request get:/{repo}/-/members/{username}/access-level

----------------------------------
* @param {ListMemberAccessLevelOfRepoParams} arg0 - listMemberAccessLevelOfRepo request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  username
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/members/${username}/access-level`,
    _apiTag: "/{repo}/-/members/{username}/access-level",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/members/{username}/access-level",
      path: {
        repo,
        username
      }
    }
  });
}