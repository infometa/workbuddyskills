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
 * @Source /{repo}/-/issues/{number}/comments
 */

/**
 * @description listIssueComments request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListIssueCommentsRes Success Response Type
 */

/**
 * @description ListIssueCommentsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:r
* @tags Issues
* @name listIssueComments
* @summary 查询仓库的 issue 评论列表。List repository issue comments.
* @request get:/{repo}/-/issues/{number}/comments

----------------------------------
* @param {ListIssueCommentsParams} arg0 - listIssueComments request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number,
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
    url: `/${repo}/-/issues/${number}/comments`,
    _apiTag: "/{repo}/-/issues/{number}/comments",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/issues/{number}/comments",
      path: {
        repo,
        number
      },
      query: query
    }
  });
}