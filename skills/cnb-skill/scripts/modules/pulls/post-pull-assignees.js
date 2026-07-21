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
 * @Source /{repo}/-/pulls/{number}/assignees
 */

/**
 * @description postPullAssignees request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostPullAssigneesRes Success Response Type
 */

/**
 * @description PostPullAssigneesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name postPullAssignees
* @summary 添加处理人到指定的合并请求。 Adds up to assignees to a pull request. Users already assigned to an issue are not replaced.
* @request post:/{repo}/-/pulls/{number}/assignees

----------------------------------
* @param {PostPullAssigneesParams} arg0 - postPullAssignees request params
* @param {ApiPostPullAssigneesForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, post_pull_assignees_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/assignees`,
    _apiTag: "/{repo}/-/pulls/{number}/assignees",
    method: "post",
    data: post_pull_assignees_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/pulls/{number}/assignees",
      path: {
        repo,
        number
      },
      body: post_pull_assignees_form
    }
  });
}