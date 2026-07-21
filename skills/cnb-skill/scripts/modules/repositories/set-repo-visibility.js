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
 * @Source /{repo}/-/settings/set_visibility
 */

/**
 * @description setRepoVisibility request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description SetRepoVisibilityRes Success Response Type
 */

/**
 * @description SetRepoVisibilityError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Repositories
* @name setRepoVisibility
* @summary 改变仓库可见性。Update visibility of repository.
* @request post:/{repo}/-/settings/set_visibility

----------------------------------
* @param {SetRepoVisibilityParams} arg0 - setRepoVisibility request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
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
    url: `/${repo}/-/settings/set_visibility`,
    _apiTag: "/{repo}/-/settings/set_visibility",
    method: "post",
    params: query,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/settings/set_visibility",
      path: {
        repo
      },
      query: query
    }
  });
}