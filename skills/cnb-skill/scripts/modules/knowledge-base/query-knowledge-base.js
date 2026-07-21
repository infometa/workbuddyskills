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
 * @Source /{repo}/-/knowledge/base/query
 */

/**
 * @description Other reuqest params
 */

/**
 * @description QueryKnowledgeBaseRes Success Response Type
 */

/**
 * @description QueryKnowledgeBaseError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags KnowledgeBase
* @name queryKnowledgeBase
* @summary 查询知识库，使用文档：https://docs.cnb.cool/zh/ai/knowledge-base.html
* @request post:/{repo}/-/knowledge/base/query

----------------------------------
* @param {string} arg0
* @param {DtoQueryKnowledgeBaseReq} arg1
* @param {RequestConfig} arg2 - Other reuqest params
*/
async function _default(repo, query, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/knowledge/base/query`,
    _apiTag: "/{repo}/-/knowledge/base/query",
    method: "post",
    data: query,
    _originParams: {
      method: "post",
      _apiTag: "/{repo}/-/knowledge/base/query",
      path: {
        repo
      },
      body: query
    }
  });
}