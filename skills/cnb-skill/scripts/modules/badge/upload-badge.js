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
 * @Source /{repo}/-/badge/upload
 */

/**
 * @description Other reuqest params
 */

/**
 * @description UploadBadgeRes Success Response Type
 */

/**
 * @description UploadBadgeError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-commit-status:rw
* @tags Badge
* @name uploadBadge
* @summary 上传徽章数据。Upload badge data
* @request post:/{repo}/-/badge/upload

----------------------------------
* @param {string} arg0
* @param {DtoUploadBadgeReq} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, request, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/badge/upload`,
    _apiTag: "/{repo}/-/badge/upload",
    method: "post",
    data: request,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/badge/upload",
      path: {
        repo
      },
      body: request
    }
  });
}