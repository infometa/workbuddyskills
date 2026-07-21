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
 * @Source /{repo}/-/files/{filePath}
 */

/**
 * @description deleteRepoFiles request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteRepoFilesRes Success Response Type
 */

/**
 * @description DeleteRepoFilesError Error Response Type
 */

/**
* @description 删除 UploadFiles 上传的附件
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-manage:rw
* @tags Pulls,Issues
* @name deleteRepoFiles
* @summary 删除 UploadFiles 上传的附件
* @request delete:/{repo}/-/files/{filePath}

----------------------------------
* @param {DeleteRepoFilesParams} arg0 - deleteRepoFiles request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  filePath
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/files/${filePath}`,
    _apiTag: "/{repo}/-/files/{filePath}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/files/{filePath}",
      path: {
        repo,
        filePath
      }
    }
  });
}