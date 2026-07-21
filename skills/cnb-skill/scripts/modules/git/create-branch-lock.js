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
 * @description createBranchLock request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description CreateBranchLockRes Success Response Type
 */

/**
 * @description CreateBranchLockError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name createBranchLock
* @summary 锁定分支
* @request post:/{repo}/-/git/branch-locks/{branch}

----------------------------------
* @param {CreateBranchLockParams} arg0 - createBranchLock request params
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
    method: "post",
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/git/branch-locks/{branch}",
      path: {
        repo,
        branch
      }
    }
  });
}