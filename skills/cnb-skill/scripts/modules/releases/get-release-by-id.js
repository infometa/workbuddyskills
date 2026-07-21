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
 * @Source /{repo}/-/releases/{release_id}
 */

/**
 * @description getReleaseByID request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetReleaseByIDRes Success Response Type
 */

/**
 * @description GetReleaseByIDError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-code:r
* @tags Releases
* @name getReleaseByID
* @summary 根据 id	查询指定 release, 包含附件信息。Get a release by id, include assets information.
* @request get:/{repo}/-/releases/{release_id}

----------------------------------
* @param {GetReleaseByIDParams} arg0 - getReleaseByID request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  release_id
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/releases/${release_id}`,
    _apiTag: "/{repo}/-/releases/{release_id}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/{repo}/-/releases/{release_id}",
      path: {
        repo,
        release_id
      }
    }
  });
}