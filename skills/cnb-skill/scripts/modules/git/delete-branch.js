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
 * @Source /{repo}/-/git/branches/{branch}
 */

/**
 * @description deleteBranch request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteBranchRes Success Response Type
 */

/**
 * @description DeleteBranchError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name deleteBranch
* @summary 删除指定分支。Delete the specified branch.
* @request delete:/{repo}/-/git/branches/{branch}

----------------------------------
* @param {DeleteBranchParams} arg0 - deleteBranch request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  branch
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/branches/${branch}`,
    _apiTag: "/{repo}/-/git/branches/{branch}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/git/branches/{branch}",
      path: {
        repo,
        branch
      }
    }
  });
}