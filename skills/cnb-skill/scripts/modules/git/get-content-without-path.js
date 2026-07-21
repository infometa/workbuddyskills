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
 * @Source /{repo}/-/git/contents
 */

/**
 * @description getContentWithoutPath request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetContentWithoutPathRes Success Response Type
 */

/**
 * @description GetContentWithoutPathError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getContentWithoutPath
* @summary 查询仓库文件和目录内容。List repository files and directories.
* @request get:/{repo}/-/git/contents

----------------------------------
* @param {GetContentWithoutPathParams} arg0 - getContentWithoutPath request params
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
    url: `/${repo}/-/git/contents`,
    _apiTag: "/{repo}/-/git/contents",
    method: "get",
    params: query,
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/contents",
      path: {
        repo
      },
      query: query
    }
  });
}