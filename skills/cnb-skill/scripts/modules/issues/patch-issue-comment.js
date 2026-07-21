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
 * @description patchIssueComment request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PatchIssueCommentRes Success Response Type
 */

/**
 * @description PatchIssueCommentError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:rw
* @tags Issues
* @name patchIssueComment
* @summary 修改一个 issue 评论。Update an issue comment.
* @request patch:/{repo}/-/issues/{number}/comments/{comment_id}

----------------------------------
* @param {PatchIssueCommentParams} arg0 - patchIssueComment request params
* @param {ApiPatchIssueCommentForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number,
  comment_id
}, patch_issue_comment_form, {
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
    method: "patch",
    data: patch_issue_comment_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/issues/{number}/comments/{comment_id}",
      path: {
        repo,
        number,
        comment_id
      },
      body: patch_issue_comment_form
    }
  });
}