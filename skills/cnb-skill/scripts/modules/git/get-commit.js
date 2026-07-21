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
 * @Source /{repo}/-/git/commits/{ref}
 */

/**
 * @description getCommit request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetCommitRes Success Response Type
 */

/**
 * @description GetCommitError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Git
* @name getCommit
* @summary 查询指定 commit。Get a commit.
* @request get:/{repo}/-/git/commits/{ref}

----------------------------------
* @param {GetCommitParams} arg0 - getCommit request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  ref
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/git/commits/${ref}`,
    _apiTag: "/{repo}/-/git/commits/{ref}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/git/commits/{ref}",
      path: {
        repo,
        ref
      }
    }
  });
}