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
 * @Source /{slug}/-/code/issues
 */

/**
 * @description listCodeIssueOpenAPI request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListCodeIssueOpenAPIRes Success Response Type
 */

/**
 * @description ListCodeIssueOpenAPIError Error Response Type
 */

/**
* @description 获取指定仓库的源码扫描问题列表，支持按问题规则和严重程度筛选
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags RepoCodeIssue
* @name listCodeIssueOpenAPI
* @summary 获取源码扫描问题列表
* @request get:/{slug}/-/code/issues

----------------------------------
* @param {ListCodeIssueOpenAPIParams} arg0 - listCodeIssueOpenAPI request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
  ...query
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${slug}/-/code/issues`,
    _apiTag: "/{slug}/-/code/issues",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/code/issues",
      path: {
        slug
      },
      query: query
    }
  });
}