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
 * @Source /{repo}/-/issues/{number}/comments/{comment_id}
 */

/**
 * @description getIssueComment request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetIssueCommentRes Success Response Type
 */

/**
 * @description GetIssueCommentError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:r
* @tags Issues
* @name getIssueComment
* @summary 获取指定 issue 评论。Get an issue comment.
* @request get:/{repo}/-/issues/{number}/comments/{comment_id}

----------------------------------
* @param {GetIssueCommentParams} arg0 - getIssueComment request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number,
  comment_id
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues/${number}/comments/${comment_id}`,
    _apiTag: "/{repo}/-/issues/{number}/comments/{comment_id}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/issues/{number}/comments/{comment_id}",
      path: {
        repo,
        number,
        comment_id
      }
    }
  });
}