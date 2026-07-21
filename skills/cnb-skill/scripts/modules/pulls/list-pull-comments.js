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
 * @Source /{repo}/-/pulls/{number}/comments
 */

/**
 * @description listPullComments request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListPullCommentsRes Success Response Type
 */

/**
 * @description ListPullCommentsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:r
* @tags Pulls
* @name listPullComments
* @summary 查询合并请求评论列表。List pull comments requests.
* @request get:/{repo}/-/pulls/{number}/comments

----------------------------------
* @param {ListPullCommentsParams} arg0 - listPullComments request params
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
    url: `/${repo}/-/pulls/${number}/comments`,
    _apiTag: "/{repo}/-/pulls/{number}/comments",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/pulls/{number}/comments",
      path: {
        repo,
        number
      },
      query: query
    }
  });
}