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
 * @Source /{repo}/-/members/{username}
 */

/**
 * @description deleteMembersOfRepo request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteMembersOfRepoRes Success Response Type
 */

/**
 * @description DeleteMembersOfRepoError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Members
* @name deleteMembersOfRepo
* @summary 删除指定仓库的直接成员。Remove direct members from specified repository.
* @request delete:/{repo}/-/members/{username}

----------------------------------
* @param {DeleteMembersOfRepoParams} arg0 - deleteMembersOfRepo request params
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
    url: `/${repo}/-/members/${username}`,
    _apiTag: "/{repo}/-/members/{username}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/members/{username}",
      path: {
        repo,
        username
      }
    }
  });
}