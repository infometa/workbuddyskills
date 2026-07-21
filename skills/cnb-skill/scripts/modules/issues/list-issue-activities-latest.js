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
 * @Source /{repo}/-/issues/{number}/activities/latest/{id}
 */

/**
 * @description listIssueActivitiesLatest request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListIssueActivitiesLatestRes Success Response Type
 */

/**
 * @description ListIssueActivitiesLatestError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:r
* @tags Issues
* @name listIssueActivitiesLatest
* @summary 查询某一动态之后的 Issue Activity
* @request get:/{repo}/-/issues/{number}/activities/latest/{id}

----------------------------------
* @param {ListIssueActivitiesLatestParams} arg0 - listIssueActivitiesLatest request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number,
  id
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues/${number}/activities/latest/${id}`,
    _apiTag: "/{repo}/-/issues/{number}/activities/latest/{id}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/issues/{number}/activities/latest/{id}",
      path: {
        repo,
        number,
        id
      }
    }
  });
}