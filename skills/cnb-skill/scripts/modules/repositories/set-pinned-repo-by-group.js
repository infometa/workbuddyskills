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
 * @Source /{slug}/-/pinned-repos
 */

/**
 * @description Other reuqest params
 */

/**
 * @description SetPinnedRepoByGroupRes Success Response Type
 */

/**
 * @description SetPinnedRepoByGroupError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* group-manage:rw
* @tags Repositories
* @name setPinnedRepoByGroup
* @summary 更新指定组织仓库墙。Update the pinned repositories of a group.
* @request put:/{slug}/-/pinned-repos

----------------------------------
* @param {string} arg0
* @param {string} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(slug, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${slug}/-/pinned-repos`,
    _apiTag: "/{slug}/-/pinned-repos",
    method: "put",
    data: request,
    _originParams: {
      method: "put",
      _apiTag: "/{slug}/-/pinned-repos",
      path: {
        slug
      },
      body: request
    }
  });
}