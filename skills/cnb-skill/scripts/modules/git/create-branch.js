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
 * @Source /{repo}/-/git/branches
 */

/**
 * @description Other reuqest params
 */

/**
 * @description CreateBranchRes Success Response Type
 */

/**
 * @description CreateBranchError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:rw
* @tags Git
* @name createBranch
* @summary 创建新分支。Create a new branch based on a start point.
* @request post:/{repo}/-/git/branches

----------------------------------
* @param {string} arg0
* @param {OpenapiCreateBranchForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, create_branch_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/branches`,
    _apiTag: "/{repo}/-/git/branches",
    method: "post",
    data: create_branch_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/git/branches",
      path: {
        repo
      },
      body: create_branch_form
    }
  });
}