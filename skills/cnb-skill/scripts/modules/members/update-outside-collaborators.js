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
 * @Source /{slug}/-/outside-collaborators/{username}
 */

/**
 * @description updateOutsideCollaborators request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description UpdateOutsideCollaboratorsRes Success Response Type
 */

/**
 * @description UpdateOutsideCollaboratorsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Members,Collaborators
* @name updateOutsideCollaborators
* @summary 更新指定仓库的外部贡献者权限信息。 Update permission information for external contributors in specified repository.
* @request put:/{slug}/-/outside-collaborators/{username}

----------------------------------
* @param {UpdateOutsideCollaboratorsParams} arg0 - updateOutsideCollaborators request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
  username,
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
    url: `/${slug}/-/outside-collaborators/${username}`,
    _apiTag: "/{slug}/-/outside-collaborators/{username}",
    method: "put",
    params: query,
    _originParams: {
      method: "put",
      _apiTag: "/{slug}/-/outside-collaborators/{username}",
      path: {
        slug,
        username
      },
      query: query
    }
  });
}