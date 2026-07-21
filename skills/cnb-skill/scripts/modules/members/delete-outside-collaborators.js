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
 * @description deleteOutsideCollaborators request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteOutsideCollaboratorsRes Success Response Type
 */

/**
 * @description DeleteOutsideCollaboratorsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Members,Collaborators
* @name deleteOutsideCollaborators
* @summary 删除指定仓库的外部贡献者。Removes external contributors from specified repository.
* @request delete:/{slug}/-/outside-collaborators/{username}

----------------------------------
* @param {DeleteOutsideCollaboratorsParams} arg0 - deleteOutsideCollaborators request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  slug,
  username
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
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{slug}/-/outside-collaborators/{username}",
      path: {
        slug,
        username
      }
    }
  });
}