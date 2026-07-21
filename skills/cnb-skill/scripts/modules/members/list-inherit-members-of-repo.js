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
 * @Source /{repo}/-/inherit-members
 */

/**
 * @description listInheritMembersOfRepo request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListInheritMembersOfRepoRes Success Response Type
 */

/**
 * @description ListInheritMembersOfRepoError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags Members
* @name listInheritMembersOfRepo
* @summary 获取指定仓库内的继承成员。List inherited members within specified repository。
* @request get:/{repo}/-/inherit-members

----------------------------------
* @param {ListInheritMembersOfRepoParams} arg0 - listInheritMembersOfRepo request params
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
    url: `/${repo}/-/inherit-members`,
    _apiTag: "/{repo}/-/inherit-members",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/inherit-members",
      path: {
        repo
      },
      query: query
    }
  });
}