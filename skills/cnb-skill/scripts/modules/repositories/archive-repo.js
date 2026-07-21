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
 * @Source /{slug}/-/settings/archive
 */

/**
 * @description Other reuqest params
 */

/**
 * @description ArchiveRepoRes Success Response Type
 */

/**
 * @description ArchiveRepoError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw,repo-code:rw
* @tags Repositories
* @name archiveRepo
* @summary 仓库归档。Archive a repository.
* @request post:/{slug}/-/settings/archive

----------------------------------
* @param {string} arg0
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default(slug, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${slug}/-/settings/archive`,
    _apiTag: "/{slug}/-/settings/archive",
    method: "post",
    _originParams: {
      method: "post",
      _apiTag: "/{slug}/-/settings/archive",
      path: {
        slug
      }
    }
  });
}