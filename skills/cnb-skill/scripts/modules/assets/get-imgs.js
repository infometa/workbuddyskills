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
 * @Source /{repo}/-/imgs/{imgPath}
 */

/**
 * @description getImgs request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetImgsRes Success Response Type
 */

/**
 * @description GetImgsError Error Response Type
 */

/**
* @description 注意：后续版本该接口可能将被移出 Assets 分类
* 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-contents:r
* @tags Assets,Pulls,Issues
* @name getImgs
* @summary 获取 issue 图片或合并请求图片的请求，返回图片二进制内容。Request to retrieve image of issues and pull requests, returns binary content.
* @request get:/{repo}/-/imgs/{imgPath}

----------------------------------
* @param {GetImgsParams} arg0 - getImgs request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  imgPath
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/imgs/${imgPath}`,
    _apiTag: "/{repo}/-/imgs/{imgPath}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/imgs/{imgPath}",
      path: {
        repo,
        imgPath
      }
    }
  });
}