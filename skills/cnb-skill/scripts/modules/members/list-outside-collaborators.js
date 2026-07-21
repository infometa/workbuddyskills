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
 * @Source /{slug}/-/outside-collaborators
 */

/**
 * @description listOutsideCollaborators request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ListOutsideCollaboratorsRes Success Response Type
 */

/**
 * @description ListOutsideCollaboratorsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:r
* @tags Members,Collaborators
* @name listOutsideCollaborators
* @summary 获取指定仓库内的外部贡献者。List external contributors in specified repository.
* @request get:/{slug}/-/outside-collaborators

----------------------------------
* @param {ListOutsideCollaboratorsParams} arg0 - listOutsideCollaborators request params
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
    url: `/${slug}/-/outside-collaborators`,
    _apiTag: "/{slug}/-/outside-collaborators",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{slug}/-/outside-collaborators",
      path: {
        slug
      },
      query: query
    }
  });
}