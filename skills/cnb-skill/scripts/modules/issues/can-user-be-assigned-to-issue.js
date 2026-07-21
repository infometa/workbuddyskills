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
 * @Source /{repo}/-/issues/{number}/assignees/{assignee}
 */

/**
 * @description canUserBeAssignedToIssue request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description CanUserBeAssignedToIssueRes Success Response Type
 */

/**
 * @description CanUserBeAssignedToIssueError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-issue:r
* @tags Issues
* @name canUserBeAssignedToIssue
* @summary 检查用户是否可以被添加到 issue 的处理人中。 Checks if a user can be assigned to an issue.
* @request get:/{repo}/-/issues/{number}/assignees/{assignee}

----------------------------------
* @param {CanUserBeAssignedToIssueParams} arg0 - canUserBeAssignedToIssue request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number,
  assignee
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/issues/${number}/assignees/${assignee}`,
    _apiTag: "/{repo}/-/issues/{number}/assignees/{assignee}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/issues/{number}/assignees/{assignee}",
      path: {
        repo,
        number,
        assignee
      }
    }
  });
}