import Imap from 'imap';
import { simpleParser } from 'mailparser';

const account = process.env.QQ_EMAIL_ACCOUNT;
const authCode = process.env.QQ_EMAIL_AUTH_CODE;

if (!account || !authCode) {
  console.error('请设置环境变量 QQ_EMAIL_ACCOUNT 和 QQ_EMAIL_AUTH_CODE');
  process.exit(1);
}

const imapConfig = {
  user: account,
  password: authCode,
  host: 'imap.qq.com',
  port: 993,
  tls: true,
  tlsOptions: { rejectUnauthorized: false },
};

function parseArgs() {
  const args = process.argv.slice(2);
  let uid = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--uid' && args[i + 1]) {
      const n = parseInt(args[i + 1].trim(), 10);
      if (!Number.isNaN(n) && n > 0) uid = n;
      i++;
    }
  }
  return { uid };
}

function openInbox(imap) {
  return new Promise((resolve, reject) => {
    imap.openBox('INBOX', false, (err, box) => {
      if (err) reject(err);
      else resolve(box);
    });
  });
}

/** 从 HTML 中粗略提取纯文本 */
function htmlToText(html) {
  if (!html || typeof html !== 'string') return '';
  return html
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .trim();
}

function getBodyText(parsed) {
  const text = parsed.text?.trim();
  if (text) return text;
  const html = parsed.html;
  if (html) return htmlToText(html);
  return '';
}

/** 按 UID 在 INBOX 中取回一封邮件的解析结果 */
async function fetchByUid(uid) {
  const imap = new Imap(imapConfig);

  return new Promise((resolve, reject) => {
    let parsed = null;
    let parseDone = null;
    const parsePromise = new Promise((r) => { parseDone = r; });

    imap.once('ready', () => {
      openInbox(imap)
        .then(() => {
          const fetch = imap.fetch(uid, { bodies: '' });
          fetch.on('message', (msg) => {
            msg.on('body', (stream) => {
              simpleParser(stream, (parseErr, result) => {
                if (!parseErr) parsed = result;
                parseDone();
              });
            });
          });
          fetch.once('error', (e) => {
            imap.end();
            reject(e);
          });
          fetch.once('end', () => {
            parsePromise.then(() => imap.end());
          });
        })
        .catch((e) => {
          imap.end();
          reject(e);
        });
    });

    imap.once('error', reject);
    imap.once('end', () => resolve(parsed));
    imap.connect();
  });
}

async function main() {
  const { uid } = parseArgs();

  if (!uid) {
    console.error('请提供 --uid，值为收信列表中的 UID');
    process.exit(1);
  }

  try {
    const email = await fetchByUid(uid);
    if (!email) {
      console.error('未找到该 UID 的邮件');
      process.exit(1);
    }
    const body = getBodyText(email);
    if (!body) {
      console.error('该邮件无正文内容');
      process.exit(1);
    }
    process.stdout.write(body);
  } catch (err) {
    console.error('获取正文失败:', err.message);
    process.exit(1);
  }
}

main();
