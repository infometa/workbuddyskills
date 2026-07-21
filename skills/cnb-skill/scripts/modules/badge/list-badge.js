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
 * @Source /{repo}/-/badge/list
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListBadgeRes Success Response Type
 */

/**
 * @description ListBadgeError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-commit-status:r
* @tags Badge
* @name listBadge
* @summary 获取徽章列表数据。List badge data
* @request get:/{repo}/-/badge/list

----------------------------------
* @param {string} arg0
* @param {DtoListBadgeReq} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/badge/list`,
    _apiTag: "/{repo}/-/badge/list",
    method: "get",
    data: request,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/badge/list",
      path: {
        repo
      },
      body: request
    }
  });
}