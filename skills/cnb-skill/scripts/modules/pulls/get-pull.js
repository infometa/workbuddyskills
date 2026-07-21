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
 * @description getPull request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetPullRes Success Response Type
 */

/**
 * @description GetPullError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:r
* @tags Pulls
* @name getPull
* @summary 查询指定合并请求。Get a pull request.
* @request get:/{repo}/-/pulls/{number}

----------------------------------
* @param {GetPullParams} arg0 - getPull request params
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
    url: `/${repo}/-/pulls/${number}`,
    _apiTag: "/{repo}/-/pulls/{number}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/pulls/{number}",
      path: {
        repo,
        number
      }
    }
  });
}