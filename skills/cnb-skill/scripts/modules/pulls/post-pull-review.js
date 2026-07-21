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
 * @Source /{repo}/-/pulls/{number}/reviews
 */

/**
 * @description postPullReview request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostPullReviewRes Success Response Type
 */

/**
 * @description PostPullReviewError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下��限。Required permissions for access token. 
* repo-notes:rw
* @tags Pulls
* @name postPullReview
* @summary 新增一次合并请求评审。Create a pull review.
* @request post:/{repo}/-/pulls/{number}/reviews

----------------------------------
* @param {PostPullReviewParams} arg0 - postPullReview request params
* @param {ApiPullReviewCreationForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, post_pull_review_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/reviews`,
    _apiTag: "/{repo}/-/pulls/{number}/reviews",
    method: "post",
    data: post_pull_review_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/pulls/{number}/reviews",
      path: {
        repo,
        number
      },
      body: post_pull_review_form
    }
  });
}