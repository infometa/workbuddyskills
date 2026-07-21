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
 * @Source /{repo}/-/pulls/{number}/assignees
 */

/**
 * @description deletePullAssignees request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeletePullAssigneesRes Success Response Type
 */

/**
 * @description DeletePullAssigneesError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name deletePullAssignees
* @summary 删除合并请求中的处理人 Removes one or more assignees from a pull request.
* @request delete:/{repo}/-/pulls/{number}/assignees

----------------------------------
* @param {DeletePullAssigneesParams} arg0 - deletePullAssignees request params
* @param {ApiDeletePullAssigneesForm} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default({
  repo,
  number
}, delete_pull_assignees_form, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/assignees`,
    _apiTag: "/{repo}/-/pulls/{number}/assignees",
    method: "delete",
    data: delete_pull_assignees_form,
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/pulls/{number}/assignees",
      path: {
        repo,
        number
      },
      body: delete_pull_assignees_form
    }
  });
}