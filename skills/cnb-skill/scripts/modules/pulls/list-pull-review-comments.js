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
 * @Source /{repo}/-/pulls/{number}/reviews/{review_id}/comments
 */

/**
 * @description listPullReviewComments request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListPullReviewCommentsRes Success Response Type
 */

/**
 * @description ListPullReviewCommentsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:r
* @tags Pulls
* @name listPullReviewComments
* @summary 查询指定合并请求评审评论列表。List pull review comments.
* @request get:/{repo}/-/pulls/{number}/reviews/{review_id}/comments

----------------------------------
* @param {ListPullReviewCommentsParams} arg0 - listPullReviewComments request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number,
  review_id,
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
    url: `/${repo}/-/pulls/${number}/reviews/${review_id}/comments`,
    _apiTag: "/{repo}/-/pulls/{number}/reviews/{review_id}/comments",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/pulls/{number}/reviews/{review_id}/comments",
      path: {
        repo,
        number,
        review_id
      },
      query: query
    }
  });
}