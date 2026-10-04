#!/usr/bin/env node

/**
 * 领取优惠券脚本
 * 用法: node receive-coupon.js [--source="领取来源"]
 */

const path = require('path');
const { receiveCouponPackages } = require('../index');

// 淡定星期四活动太阳码图片：远程链接（优先，Markdown 可直接渲染）与本地文件（兜底，配合平台图片发送机制）
const THURSDAY_QRCODE_URL = 'https://otherfiles.uupt.com/skills/thursday-qrcode.jpg';
const THURSDAY_QRCODE_FILE = path.join(__dirname, '..', 'assets', 'thursday-qrcode.jpg');

// 解析命令行参数
function parseArgs() {
  const args = {};
  process.argv.slice(2).forEach(arg => {
    const match = arg.match(/^--(\w+)=(.+)$/);
    if (match) {
      args[match[1]] = match[2].replace(/^["']|["']$/g, '');
    }
  });
  return args;
}

async function main() {
  const args = parseArgs();

  try {
    const result = await receiveCouponPackages({
      source: args.source
    });

    if (!result) {
      console.error('执行失败: 未获取到接口返回');
      process.exit(1);
    }

    console.log('📊 领券结果:');
    console.log(JSON.stringify(result, null, 2));

    if (result.body) {
      const body = result.body;
      const couponList = Array.isArray(body.couponList) ? body.couponList : [];

      console.log('\n[COUPON_RESULT]');
      console.log(`NEWLY_CLAIMED=${body.newlyClaimed === true}`);
      console.log(`COUPON_COUNT=${couponList.length}`);
      if (body.thursdayJoinAble === true) {
        console.log('THURSDAY_JOIN_ABLE=true');
        console.log(`THURSDAY_QRCODE_URL=${THURSDAY_QRCODE_URL}`);
        console.log(`THURSDAY_QRCODE_FILE=${THURSDAY_QRCODE_FILE}`);
      }
      console.log('\n💡 提示: Agent 请根据 SKILL.md 场景六的触发条件（newlyClaimed / couponList / thursdayJoinAble）选择对应话术模板回复用户。');
    } else {
      console.error(`\n❌ 领券失败: ${result.msg || result.message || '未知错误'}`);
      process.exit(1);
    }
  } catch (error) {
    console.error('执行失败:', error.message);
    process.exit(1);
  }
}

main();
