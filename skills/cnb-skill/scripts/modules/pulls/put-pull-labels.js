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
 * @description putPullLabels request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description PutPullLabelsRes Success Response Type
 */

/**
 * @description PutPullLabelsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name putPullLabels
* @summary 设置合并请求标签。Set the new labels for a pull.
* @request put:/{repo}/-/pulls/{number}/labels

----------------------------------
* @param {PutPullLabelsParams} arg0 - putPullLabels request params
* @param {ApiPutPullLabelsForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, put_pull_labels_form, {
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
    method: "put",
    data: put_pull_labels_form,
    _originParams: {
      method: "put",
      _apiTag: "/{repo}/-/pulls/{number}/labels",
      path: {
        repo,
        number
      },
      body: put_pull_labels_form
    }
  });
}