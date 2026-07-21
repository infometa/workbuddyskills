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
 * @Source /{repo}/-/pulls
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostPullRes Success Response Type
 */

/**
 * @description PostPullError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name postPull
* @summary 新增一个合并请求。Create a pull request.
* @request post:/{repo}/-/pulls

----------------------------------
* @param {string} arg0
* @param {ApiPullCreationForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, post_pull_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls`,
    _apiTag: "/{repo}/-/pulls",
    method: "post",
    data: post_pull_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/pulls",
      path: {
        repo
      },
      body: post_pull_form
    }
  });
}