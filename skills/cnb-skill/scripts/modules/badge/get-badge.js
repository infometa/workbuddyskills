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
 * @Source /{repo}/-/badge/git/{sha}/{badge}
 */

/**
 * @description getBadge request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetBadgeRes Success Response Type
 */

/**
 * @description GetBadgeError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-commit-status:r
* @tags Badge
* @name getBadge
* @summary 获取徽章 svg 或 JSON 数据。Get badge svg or JSON data.
* @request get:/{repo}/-/badge/git/{sha}/{badge}

----------------------------------
* @param {GetBadgeParams} arg0 - getBadge request params
* @param {DtoGetBadgeReq} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  sha,
  badge
}, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/badge/git/${sha}/${badge}`,
    _apiTag: "/{repo}/-/badge/git/{sha}/{badge}",
    method: "get",
    data: request,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/badge/git/{sha}/{badge}",
      path: {
        repo,
        sha,
        badge
      },
      body: request
    }
  });
}