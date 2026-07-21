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
 * @Source /{repo}/-/pulls/{number}/merge
 */

/**
 * @description mergePull request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description MergePullRes Success Response Type
 */

/**
 * @description MergePullError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name mergePull
* @summary 合并一个合并请求。Merge a pull request.
* @request put:/{repo}/-/pulls/{number}/merge

----------------------------------
* @param {MergePullParams} arg0 - mergePull request params
* @param {ApiMergePullRequest} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, merge_pull_request_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/merge`,
    _apiTag: "/{repo}/-/pulls/{number}/merge",
    method: "put",
    data: merge_pull_request_form,
    _originParams: {
      method: "put",
      _apiTag: "/{repo}/-/pulls/{number}/merge",
      path: {
        repo,
        number
      },
      body: merge_pull_request_form
    }
  });
}