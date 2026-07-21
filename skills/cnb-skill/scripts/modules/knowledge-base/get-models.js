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
 * @Source /{repo}/-/knowledge/embedding/models
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetModelsRes Success Response Type
 */

/**
 * @description GetModelsError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags KnowledgeBase
* @name getModels
* @summary 获取当前支持的 Embedding 模型列表
* @request get:/{repo}/-/knowledge/embedding/models

----------------------------------
* @param {string} arg0
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default(repo, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/knowledge/embedding/models`,
    _apiTag: "/{repo}/-/knowledge/embedding/models",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/knowledge/embedding/models",
      path: {
        repo
      }
    }
  });
}