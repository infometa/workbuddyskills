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
 * @Source /{repo}/-/pulls/{number}/assignees/{assignee}
 */

/**
 * @description canUserBeAssignedToPull request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description CanUserBeAssignedToPullRes Success Response Type
 */

/**
 * @description CanUserBeAssignedToPullError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:r
* @tags Pulls
* @name canUserBeAssignedToPull
* @summary 检查用户是否可以被添加到合并请求的处理人中。 Checks if a user can be assigned to a pull request.
* @request get:/{repo}/-/pulls/{number}/assignees/{assignee}

----------------------------------
* @param {CanUserBeAssignedToPullParams} arg0 - canUserBeAssignedToPull request params
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
    url: `/${repo}/-/pulls/${number}/assignees/${assignee}`,
    _apiTag: "/{repo}/-/pulls/{number}/assignees/{assignee}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/pulls/{number}/assignees/{assignee}",
      path: {
        repo,
        number,
        assignee
      }
    }
  });
}