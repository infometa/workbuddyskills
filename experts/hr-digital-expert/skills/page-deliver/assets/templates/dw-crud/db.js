/**
 * 双模式存储模块
 *
 * - 有 MONGO_URI 环境变量：使用 MongoDB（生产环境）
 * - 无 MONGO_URI：使用本地 JSON 文件（本地预览零依赖）
 */

const path = require('path');
const fs = require('fs');

const PROJECT_ID = '{{PROJECT_ID}}';
const MONGO_URI = process.env.MONGO_URI && `${process.env.MONGO_URI}/${PROJECT_ID}`;
const DATA_FILE = path.join(__dirname, 'data', 'db.json');

let mode = 'json';
let mongoose = null;
let Model = null;

function readJSON() {
  try {
    if (!fs.existsSync(DATA_FILE)) return [];
    return JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
  } catch { return []; }
}

function writeJSON(data) {
  const dir = path.dirname(DATA_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2), 'utf-8');
}

async function init() {
  if (MONGO_URI) {
    try {
      mongoose = require('mongoose');
      await mongoose.connect(MONGO_URI);
      // TODO: 定义 Schema
      mode = 'mongodb';
      console.log(`[db] MongoDB connected: ${PROJECT_ID}`);
    } catch (e) {
      console.warn(`[db] MongoDB 连接失败，降级到 JSON 模式: ${e.message}`);
      mode = 'json';
    }
  } else {
    console.log('[db] JSON file mode (no MONGO_URI)');
  }
}

async function findAll(filter = {}) {
  if (mode === 'mongodb') return Model.find(filter).lean();
  return readJSON();
}

async function create(doc) {
  if (mode === 'mongodb') return (await Model.create(doc)).toObject();
  const items = readJSON();
  const newItem = { id: Date.now().toString(36), ...doc, createdAt: new Date().toISOString() };
  items.push(newItem);
  writeJSON(items);
  return newItem;
}

async function update(id, updates) {
  if (mode === 'mongodb') return Model.findByIdAndUpdate(id, updates, { new: true }).lean();
  const items = readJSON();
  const idx = items.findIndex(i => i.id === id);
  if (idx === -1) return null;
  items[idx] = { ...items[idx], ...updates, updatedAt: new Date().toISOString() };
  writeJSON(items);
  return items[idx];
}

async function remove(id) {
  if (mode === 'mongodb') return Model.findByIdAndDelete(id);
  const items = readJSON();
  writeJSON(items.filter(i => i.id !== id));
}

module.exports = { init, findAll, create, update, remove };
