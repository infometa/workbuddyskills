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
 * @description listBranches request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListBranchesRes Success Response Type
 */

/**
 * @description ListBranchesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name listBranches
* @summary 查询分支列表。List branches.
* @request get:/{repo}/-/git/branches

----------------------------------
* @param {ListBranchesParams} arg0 - listBranches request params
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
    url: `/${repo}/-/git/branches`,
    _apiTag: "/{repo}/-/git/branches",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/branches",
      path: {
        repo
      },
      query: query
    }
  });
}