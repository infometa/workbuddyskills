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
 * @Source /user/stared-repos
 */

/**
 * @description getUserAllStaredRepos request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetUserAllStaredReposRes Success Response Type
 */

/**
 * @description GetUserAllStaredReposError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* account-engage:r
* @tags Starring
* @name getUserAllStaredRepos
* @summary 获取当前用户 star 的仓库列表���List all stared repositories.
* @request get:/user/stared-repos

----------------------------------
* @param {GetUserAllStaredReposParams} arg0 - getUserAllStaredRepos request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
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
    url: "/user/stared-repos",
    _apiTag: "/user/stared-repos",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/user/stared-repos",
      query: query
    }
  });
}