const express = require('express');
const cors = require('cors');
const path = require('path');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() });
});

// TODO: CRUD API 路由
// 示例：
// app.get('/api/items', async (req, res) => {
//   const items = await db.findAll();
//   res.json(items);
// });
//
// app.post('/api/items', async (req, res) => {
//   const item = await db.create(req.body);
//   res.json(item);
// });
//
// app.put('/api/items/:id', async (req, res) => {
//   const item = await db.update(req.params.id, req.body);
//   res.json(item);
// });
//
// app.delete('/api/items/:id', async (req, res) => {
//   await db.remove(req.params.id);
//   res.json({ success: true });
// });

// SPA 兜底
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 初始化数据库连接后启动
db.init().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
});
