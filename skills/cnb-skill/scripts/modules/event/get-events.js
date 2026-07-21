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
 * @Source /events/{repo}/-/{date}
 */

/**
 * @description getEvents request params
 */

/**
 * @description Other reuqest params
 */

/**
 * @description GetEventsRes Success Response Type
 */

/**
 * @description GetEventsError Error Response Type
 */

/**
* @description No description
* @tags Event
* @name getEvents
* @summary 获取仓库动态预签名地址，并返回内容。Get events pre-signed URL and return content.
* @request get:/events/{repo}/-/{date}

----------------------------------
* @param {GetEventsParams} arg0 - getEvents request params
* @param {RequestConfig} arg1 - Other reuqest params
*/
async function _default({
  repo,
  date
}, {
  req,
  options,
  ...axiosConfig
} = {}) {
  return await _core.default.request({
    ...axiosConfig,
    _next_req: req,
    options: options,
    url: `/events/${repo}/-/${date}`,
    _apiTag: "/events/{repo}/-/{date}",
    method: "get",
    _originParams: {
      method: "get",
      _apiTag: "/events/{repo}/-/{date}",
      path: {
        repo,
        date
      }
    }
  });
}