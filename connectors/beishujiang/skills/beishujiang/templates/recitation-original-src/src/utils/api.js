/**
 * 本地 mock 接口层 — 替代原项目的 @/utils/api(bookApi / readConfigApi)
 *
 * 方法签名、入参、返回结构({ code, msg, data })与真实后端保持一致,
 * 数据保存在内存中；存在 material.js 注入时优先展示确认后的分页材料。
 *
 * 如需接回真实后端:用原项目的 src/utils/api.js + request.js 替换本文件即可,
 * RecitePage.vue / CzModal.vue 无需改动。
 */

import { getInjectedMaterial, createMaterialBook } from './recitation-material'

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

// ──────────────── 示例书籍数据 ────────────────
// 结构与后端一致:合集(collection) → 章节(chapter) → 内容块(bookDataList)

// 演示用图片:内联 SVG 转成 dataURL(IMG 块)
const demoImgUrl = 'data:image/svg+xml;utf8,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="560" height="220">' +
  '<rect width="560" height="220" rx="12" fill="#eef3ff"/>' +
  '<rect x="60" y="40" width="120" height="140" rx="4" fill="#5b7cfa"/>' +
  '<rect x="200" y="80" width="120" height="100" rx="4" fill="#8f6bf5"/>' +
  '<rect x="340" y="60" width="120" height="120" rx="4" fill="#f5a65b"/>' +
  '<text x="280" y="205" font-size="14" fill="#667" text-anchor="middle" font-family="sans-serif">示例插图(本地 mock)</text>' +
  '</svg>'
)

// 章节数据。TXT 块展示 richTxt(富文本 HTML),TABLE 块展示 txt(markdown),IMG 块走 objKey→URL
const books = {
  'demo-book-1': {
    title: '岳阳楼记 + 数学笔记(演示文档)',
    chapters: [
      {
        id: 'demo-ch-1',
        title: '第一章 · 岳阳楼记(上)',
        blocks: [
          {
            id: 'demo-blk-1-1',
            title: '开篇 · 谪守巴陵',
            dataBaseBean: {
              bookDataType: 'TXT',
              richTxt: '<p>庆历四年春,滕子京谪守巴陵郡。越明年,政通人和,百废具兴,乃重修岳阳楼,增其旧制,刻唐贤今人诗赋于其上,属予作文以记之。</p>',
              txt: '庆历四年春,滕子京谪守巴陵郡。越明年,政通人和,百废具兴,乃重修岳阳楼,增其旧制,刻唐贤今人诗赋于其上,属予作文以记之。'
            }
          },
          {
            id: 'demo-blk-1-2',
            title: '总写 · 巴陵胜状',
            dataBaseBean: {
              bookDataType: 'TXT',
              richTxt: '<p>予观夫巴陵胜状,在洞庭一湖。衔远山,吞长江,浩浩汤汤,横无际涯,朝晖夕阴,气象万千,此则岳阳楼之大观也,前人之述备矣。</p><p>然则北通巫峡,南极潇湘,迁客骚人,多会于此,览物之情,得无异乎?</p>',
              txt: '予观夫巴陵胜状,在洞庭一湖。衔远山,吞长江,浩浩汤汤,横无际涯,朝晖夕阴,气象万千,此则岳阳楼之大观也,前人之述备矣。然则北通巫峡,南极潇湘,迁客骚人,多会于此,览物之情,得无异乎?'
            }
          },
          {
            id: 'demo-blk-1-3',
            title: '英语单词 · 附注',
            dataBaseBean: {
              bookDataType: 'TXT',
              richTxt: '<p>本段包含 English words 与数字,便于测试规则挖空(数字 / 英文):</p><p>In 1046, Teng Zijing rebuilt the Yueyang Tower. The lake covers about 2,820 square kilometers, and its depth is 6.7 meters on average.</p>',
              txt: '本段包含 English words 与数字,便于测试规则挖空(数字 / 英文):In 1046, Teng Zijing rebuilt the Yueyang Tower. The lake covers about 2,820 square kilometers, and its depth is 6.7 meters on average.'
            }
          }
        ]
      },
      {
        id: 'demo-ch-2',
        title: '第二章 · 岳阳楼记(下)',
        blocks: [
          {
            id: 'demo-blk-2-1',
            title: '若夫 · 阴雨之悲',
            dataBaseBean: {
              bookDataType: 'TXT',
              richTxt: '<p>若夫淫雨霏霏,连月不开,阴风怒号,浊浪排空,日星隐曜,山岳潜形,商旅不行,樯倾楫摧,薄暮冥冥,虎啸猿啼。登斯楼也,则有去国怀乡,忧谗畏讥,满目萧然,感极而悲者矣。</p>',
              txt: '若夫淫雨霏霏,连月不开,阴风怒号,浊浪排空,日星隐曜,山岳潜形,商旅不行,樯倾楫摧,薄暮冥冥,虎啸猿啼。登斯楼也,则有去国怀乡,忧谗畏讥,满目萧然,感极而悲者矣。'
            }
          },
          {
            id: 'demo-blk-2-2',
            title: '至若 · 春和之喜',
            dataBaseBean: {
              bookDataType: 'TXT',
              richTxt: '<p>至若春和景明,波澜不惊,上下天光,一碧万顷,沙鸥翔集,锦鳞游泳,岸芷汀兰,郁郁青青。而或长烟一空,皓月千里,浮光跃金,静影沉璧,渔歌互答,此乐何极!登斯楼也,则有心旷神怡,宠辱偕忘,把酒临风,其喜洋洋者矣。</p>',
              txt: '至若春和景明,波澜不惊,上下天光,一碧万顷,沙鸥翔集,锦鳞游泳,岸芷汀兰,郁郁青青。而或长烟一空,皓月千里,浮光跃金,静影沉璧,渔歌互答,此乐何极!登斯楼也,则有心旷神怡,宠辱偕忘,把酒临风,其喜洋洋者矣。'
            }
          },
          {
            id: 'demo-blk-2-3',
            title: '嗟夫 · 先忧后乐',
            dataBaseBean: {
              bookDataType: 'TXT',
              richTxt: '<p>嗟夫!予尝求古仁人之心,或异二者之为,何哉?不以物喜,不以己悲,居庙堂之高则忧其民,处江湖之远则忧其君。</p><p>是进亦忧,退亦忧。然则何时而乐耶?其必曰「先天下之忧而忧,后天下之乐而乐」乎!噫!微斯人,吾谁与归?</p><p>时六年九月十五日。</p>',
              txt: '嗟夫!予尝求古仁人之心,或异二者之为,何哉?不以物喜,不以己悲,居庙堂之高则忧其民,处江湖之远则忧其君。是进亦忧,退亦忧。然则何时而乐耶?其必曰「先天下之忧而忧,后天下之乐而乐」乎!噫!微斯人,吾谁与归?时六年九月十五日。'
            }
          }
        ]
      },
      {
        id: 'demo-ch-3',
        title: '第三章 · 数学笔记(公式示例)',
        blocks: [
          {
            id: 'demo-blk-3-1',
            title: '勾股定理',
            dataBaseBean: {
              bookDataType: 'TXT',
              richTxt: '<p>直角三角形两直角边 $a$、$b$,斜边 $c$,满足 $a^2 + b^2 = c^2$。</p><p>常用变形:$c = \\sqrt{a^2 + b^2}$,面积 $S = \\dfrac{1}{2}ab$。</p>',
              txt: '直角三角形两直角边 a、b,斜边 c,满足 a^2 + b^2 = c^2。常用变形:c = sqrt(a^2+b^2),面积 S = (1/2)ab。'
            }
          },
          {
            id: 'demo-blk-3-2',
            title: '公式速查表',
            dataBaseBean: {
              bookDataType: 'TABLE',
              txt: '| 名称 | 公式 | 备注 |\n| --- | --- | --- |\n| 勾股定理 | $a^2 + b^2 = c^2$ | 直角三角形 |\n| 圆的面积 | $S = \\pi r^2$ | $r$ 为半径 |\n| 欧拉公式 | $e^{i\\pi} + 1 = 0$ | 最美公式 |',
              richTxt: ''
            }
          },
          {
            id: 'demo-blk-3-3',
            title: '示例插图',
            dataBaseBean: {
              bookDataType: 'IMG',
              resourceDataBean: { objId: 'demo-obj-1', objKey: 'demo-key-1' }
            }
          }
        ]
      }
    ]
  }
}

const injectedMaterial = getInjectedMaterial()
if (injectedMaterial) books['imported-book'] = createMaterialBook(injectedMaterial)

// objKey → 图片 URL 缓存(IMG 块展示用)
const objUrlMap = new Map([['demo-key-1', demoImgUrl]])

// 阅读配置(CzModal 挖空设置持久化,保存在内存)
const hollowConfig = { hollowType: 1, density: 30, keyWords: 0, wordUnit: 1, intervalType: 1, interval: '3', hide: '3' }

const ok = (data) => ({ code: 0, data })

// ──────────────── 本地 AI 实现 ────────────────

// 中文停用字:用于把连续汉字切成「词」片段
const STOP_CHARS = new Set('的了是在我和你他她它个也都要就还很被把让向着于从中上下里外去过但而若夫之其此那为以所可能会将不地得'.split(''))

// 从纯文本里提取候选关键词及下标区间(英文单词 / 数字 / 汉字片段)
function extractKeywords(article) {
  const ranges = []
  const re = /[A-Za-z][A-Za-z'-]*|\d+(?:[.,]\d+)*%?|[\u4e00-\u9fa5]+/g
  let m
  while ((m = re.exec(article))) {
    const text = m[0]
    if (/[\u4e00-\u9fa5]/.test(text)) {
      // 汉字串按停用字切成 2~5 字的片段
      let start = m.index
      let frag = ''
      const push = () => {
        if (frag.length >= 2) ranges.push([start - frag.length, start])
        frag = ''
      }
      for (const ch of text) {
        if (STOP_CHARS.has(ch)) { push(); start++ }
        else { frag += ch; start++ }
      }
      push()
    } else {
      ranges.push([m.index, m.index + text.length])
    }
  }
  return ranges.filter(([s, e]) => e - s >= 2)
}

// 本地版 AI 挖空:按已保存的密度(或 keyWords 个数)均匀挑关键词
function localWordHollow(article, keyWords) {
  const all = extractKeywords(article)
  if (!all.length) return { wordIndexBeans: [] }
  let picked
  if (keyWords > 0) {
    const n = Math.min(keyWords, all.length)
    picked = all.filter((_, i) => i % Math.max(1, Math.floor(all.length / n)) === 0).slice(0, n)
  } else {
    const density = Math.max(10, Math.min(90, hollowConfig.density)) / 100
    picked = all.filter((_, i) => i % Math.max(1, Math.round(1 / density)) === 0)
  }
  // 相同关键词文本合并到一个 wordIndexBean,多处出现放进 strIndexBeans
  const byText = new Map()
  picked.forEach(([s, e]) => {
    const t = article.slice(s, e)
    if (!byText.has(t)) byText.set(t, [])
    byText.get(t).push({ startIndex: s, endIndex: e })
  })
  return { wordIndexBeans: Array.from(byText.entries()).map(([word, strIndexBeans]) => ({ word, strIndexBeans })) }
}

// 本地版 AI 分块:按句号/问叹号切句,凑满 maxChars 为一块
function localGenerateBlock(text, maxChars) {
  const limit = maxChars > 0 ? maxChars : 200
  const sentences = String(text).split(/(?<=[。!?!?;;\n])/)
  const chunks = []
  let cur = ''
  sentences.forEach(s => {
    if (cur && (cur + s).length > limit) { chunks.push(cur); cur = s }
    else cur += s
  })
  if (cur.trim()) chunks.push(cur)
  return chunks.map(c => c.trim()).filter(Boolean)
}

// ──────────────── mock bookApi(签名与真实接口一致) ────────────────

function findChapter(id) {
  for (const book of Object.values(books)) {
    const ch = book.chapters.find(c => c.id === String(id))
    if (ch) return ch
  }
  return null
}

// 提交的扁平块结构 → 回存为嵌套结构(与后端加载格式一致)
const toStoredBlocks = (list) => (list || []).map((blk, i) => ({
  id: `demo-blk-${Date.now().toString(36)}-${i}`,
  title: blk.title || `文本块 ${i + 1}`,
  dataBaseBean: {
    bookDataType: blk.bookDataType || 'TXT',
    richTxt: blk.richTxt || '',
    txt: blk.txt || '',
    resourceDataBean: blk.resourceDataBean || null
  }
}))

export const bookApi = {
  /** 合集下章节目录 */
  async getChapterList(params) {
    await delay(150)
    const book = books[params && params.collectionId]
    if (!book) return { code: 1, msg: '书籍不存在' }
    return ok(book.chapters.map(ch => ({ id: ch.id, title: ch.title, pageNumber: ch.pageNumber })))
  },

  /** 章节详情(内容块列表) */
  async getDetail(params) {
    await delay(200)
    const ch = findChapter(params && params.id)
    if (!ch) return { code: 1, msg: '章节不存在' }
    return ok({ bookDataList: ch.blocks })
  },

  /** 保存章节内容(全量更新;无 id 时为新增书籍) */
  async saveBook(data) {
    await delay(400)
    if (data && data.id) {
      const ch = findChapter(data.id)
      if (!ch) return { code: 1, msg: '章节不存在' }
      ch.blocks = toStoredBlocks(data.data)
      return ok({ parentBookId: undefined })
    }
    // 新增书籍:建一个合集 + 一个章节,后续按 id 正常加载
    const stamp = Date.now().toString(36)
    const bookId = `demo-book-${stamp}`
    books[bookId] = {
      title: (data && data.title) || '未命名材料',
      chapters: [{
        id: `demo-ch-${stamp}`,
        title: (data && data.title) || '第一章',
        blocks: toStoredBlocks(data && data.data)
      }]
    }
    return ok({ parentBookId: bookId })
  },

  /** 更新分块标题 */
  async updateBlockTitle(id, title, bookId) {
    await delay(150)
    for (const book of Object.values(books)) {
      for (const ch of book.chapters) {
        const blk = ch.blocks.find(b => b.id === String(id))
        if (blk) { blk.title = title; return ok(null) }
      }
    }
    return { code: 1, msg: '块不存在' }
  },

  /** AI 生成分块标题(本地实现:取块内容前几个字) */
  async aiGenerateBlockTitle(id) {
    await delay(1200)
    for (const book of Object.values(books)) {
      for (const ch of book.chapters) {
        const blk = ch.blocks.find(b => b.id === String(id))
        if (blk) {
          const text = (blk.dataBaseBean.richTxt || blk.dataBaseBean.txt || '').replace(/<[^>]+>/g, '')
          return ok(text.slice(0, 8) || 'AI 摘要')
        }
      }
    }
    return { code: 1, msg: '块不存在' }
  },

  /** 上传图片 → ResourceDataBean(objId/objKey) */
  async uploadImg(file) {
    await delay(300)
    const url = await new Promise(resolve => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.readAsDataURL(file)
    })
    const objId = 'obj-' + Date.now()
    const objKey = 'key-' + Date.now()
    objUrlMap.set(objKey, url)
    return ok([{ objId, objKey }])
  },

  /** objKey → 图片访问 URL */
  async objToUrl(objKey) {
    await delay(100)
    const url = objUrlMap.get(objKey)
    return url ? ok(url) : { code: 1, msg: '资源不存在' }
  },

  /** AI 挖空(本地实现,返回结构与后端一致) */
  async batchWordHollow(data) {
    await delay(900)
    const list = (data && data.batchWordHollow) || []
    return ok(list.map(it => ({
      id: it.id,
      wordHollow: localWordHollow(it.article || '', data.keyWords || 0)
    })))
  },

  /** AI 分块(本地实现,返回结构与后端一致) */
  async generateBlock(blocks, maxChars = 0) {
    await delay(900)
    return ok((blocks || []).map(text => localGenerateBlock(text, maxChars)))
  }
}

// ──────────────── mock readConfigApi(CzModal 挖空配置) ────────────────

export const readConfigApi = {
  async getConfigWordHollow() {
    await delay(100)
    return ok({ ...hollowConfig })
  },
  async updateWordHollow(data) {
    await delay(200)
    Object.assign(hollowConfig, data)
    return ok(null)
  }
}
