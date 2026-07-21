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
 * @Source /{repo}/-/pulls/{number}/labels/{name}
 */

/**
 * @description deletePullLabel request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeletePullLabelRes Success Response Type
 */

/**
 * @description DeletePullLabelError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-pr:rw
* @tags Pulls
* @name deletePullLabel
* @summary 删除合并请求标签。Remove a label from a pull.
* @request delete:/{repo}/-/pulls/{number}/labels/{name}

----------------------------------
* @param {DeletePullLabelParams} arg0 - deletePullLabel request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  number,
  name
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/pulls/${number}/labels/${name}`,
    _apiTag: "/{repo}/-/pulls/{number}/labels/{name}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/pulls/{number}/labels/{name}",
      path: {
        repo,
        number,
        name
      }
    }
  });
}