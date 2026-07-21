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
 * @Source /{repo}/-/pulls/{number}
 */

/**
 * @description patchPull request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PatchPullRes Success Response Type
 */

/**
 * @description PatchPullError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name patchPull
* @summary 更新一个合并请求。Update a pull request.
* @request patch:/{repo}/-/pulls/{number}

----------------------------------
* @param {PatchPullParams} arg0 - patchPull request params
* @param {ApiPatchPullRequest} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, update_pull_request_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}`,
    _apiTag: "/{repo}/-/pulls/{number}",
    method: "patch",
    data: update_pull_request_form,
    _originParams: {
      method: "patch",
      _apiTag: "/{repo}/-/pulls/{number}",
      path: {
        repo,
        number
      },
      body: update_pull_request_form
    }
  });
}