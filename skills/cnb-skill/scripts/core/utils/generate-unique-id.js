"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.generateUniqueId = generateUniqueId;
function generateUniqueId() {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}
;