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
 * @Source /{repo}/-/git/branch-locks/{branch}
 */

/**
 * @description deleteBranchLock request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteBranchLockRes Success Response Type
 */

/**
 * @description DeleteBranchLockError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name deleteBranchLock
* @summary 解除锁定分支
* @request delete:/{repo}/-/git/branch-locks/{branch}

----------------------------------
* @param {DeleteBranchLockParams} arg0 - deleteBranchLock request params
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
    url: `/${repo}/-/git/branch-locks/${branch}`,
    _apiTag: "/{repo}/-/git/branch-locks/{branch}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/git/branch-locks/{branch}",
      path: {
        repo,
        branch
      }
    }
  });
}