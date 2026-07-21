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
 * @Source /{repo}/-/pulls/{number}/comments/{comment_id}
 */

/**
 * @description patchPullComment request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PatchPullCommentRes Success Response Type
 */

/**
 * @description PatchPullCommentError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:rw
* @tags Pulls
* @name patchPullComment
* @summary 更新一个合并请求评论。Update a pull comment.
* @request patch:/{repo}/-/pulls/{number}/comments/{comment_id}

----------------------------------
* @param {PatchPullCommentParams} arg0 - patchPullComment request params
* @param {ApiPatchPullCommentForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number,
  comment_id
}, patch_pull_comment_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/comments/${comment_id}`,
    _apiTag: "/{repo}/-/pulls/{number}/comments/{comment_id}",
    method: "patch",
    data: patch_pull_comment_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/pulls/{number}/comments/{comment_id}",
      path: {
        repo,
        number,
        comment_id
      },
      body: patch_pull_comment_form
    }
  });
}