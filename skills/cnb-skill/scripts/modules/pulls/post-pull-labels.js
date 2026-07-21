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
 * @Source /{repo}/-/pulls/{number}/labels
 */

/**
 * @description postPullLabels request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PostPullLabelsRes Success Response Type
 */

/**
 * @description PostPullLabelsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name postPullLabels
* @summary 新增合并请求标签。Add labels to a pull.
* @request post:/{repo}/-/pulls/{number}/labels

----------------------------------
* @param {PostPullLabelsParams} arg0 - postPullLabels request params
* @param {ApiPostPullLabelsForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, post_pull_labels_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/labels`,
    _apiTag: "/{repo}/-/pulls/{number}/labels",
    method: "post",
    data: post_pull_labels_form,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/pulls/{number}/labels",
      path: {
        repo,
        number
      },
      body: post_pull_labels_form
    }
  });
}