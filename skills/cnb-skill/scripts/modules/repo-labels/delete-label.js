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
 * @Source /{repo}/-/labels/{name}
 */

/**
 * @description deleteLabel request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description DeleteLabelRes Success Response Type
 */

/**
 * @description DeleteLabelError Error Response Type
 */

/**
* @description 访问令牌调用此接口需包含以下权限。Required permissions for access token. 
* repo-notes:rw
* @tags RepoLabels
* @name deleteLabel
* @summary 删除指定的仓库标签。Delete the specified repository label.
* @request delete:/{repo}/-/labels/{name}

----------------------------------
* @param {DeleteLabelParams} arg0 - deleteLabel request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  name
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/${repo}/-/labels/${name}`,
    _apiTag: "/{repo}/-/labels/{name}",
    method: "delete",
    _originParams: {
      method: "delete",
      _apiTag: "/{repo}/-/labels/{name}",
      path: {
        repo,
        name
      }
    }
  });
}