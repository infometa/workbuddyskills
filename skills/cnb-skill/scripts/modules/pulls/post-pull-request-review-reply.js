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
 * @Source /{repo}/-/pulls/{number}/reviews/{review_id}/replies
 */

/**
 * @description postPullRequestReviewReply request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostPullRequestReviewReplyRes Success Response Type
 */

/**
 * @description PostPullRequestReviewReplyError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:rw
* @tags Pulls
* @name postPullRequestReviewReply
* @summary 回复一个 review 评审
* @request post:/{repo}/-/pulls/{number}/reviews/{review_id}/replies

----------------------------------
* @param {PostPullRequestReviewReplyParams} arg0 - postPullRequestReviewReply request params
* @param {ApiPostPullRequestReviewReplyForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number,
  review_id
}, post_pull_request_review_reply_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/reviews/${review_id}/replies`,
    _apiTag: "/{repo}/-/pulls/{number}/reviews/{review_id}/replies",
    method: "post",
    data: post_pull_request_review_reply_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/pulls/{number}/reviews/{review_id}/replies",
      path: {
        repo,
        number,
        review_id
      },
      body: post_pull_request_review_reply_form
    }
  });
}