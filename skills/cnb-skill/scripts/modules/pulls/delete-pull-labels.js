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
 * @description deletePullLabels request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeletePullLabelsRes Success Response Type
 */

/**
 * @description DeletePullLabelsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name deletePullLabels
* @summary 清空合并请求标签。Remove all labels from a pull.
* @request delete:/{repo}/-/pulls/{number}/labels

----------------------------------
* @param {DeletePullLabelsParams} arg0 - deletePullLabels request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number
}, {
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
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/pulls/{number}/labels",
      path: {
        repo,
        number
      }
    }
  });
}