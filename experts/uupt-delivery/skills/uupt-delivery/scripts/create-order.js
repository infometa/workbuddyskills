#!/usr/bin/env node

/**
 * 创建订单脚本
 * 用法: node create-order.js --priceToken="询价token" --receiverPhone="收件人电话" [--channel="渠道"] [--note="帮帮内容"]
 */

const { createOrder, formatPrice, CONFIG_DIR } = require('../index');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

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
  
  if (!args.priceToken || !args.receiverPhone) {
    console.log(`
📦 创建订单

用法:
  node create-order.js --priceToken="询价token" --receiverPhone="收件人电话" [--channel="渠道"] [--note="帮帮内容"]

参数:
  --priceToken     询价接口返回的 token（必填）
  --receiverPhone  收件人手机号（必填）
  --channel        聊天渠道（可选，如 wechat、feishu、dingtalk 等）
  --note           帮帮内容描述（帮帮订单时必填，描述具体需要跑男提供的帮助服务）

示例:
  # 跑腿配送
  node create-order.js --priceToken="abc123xyz" --receiverPhone="13800138000"
  node create-order.js --priceToken="abc123xyz" --receiverPhone="13800138000" --channel="wechat"
  # 帮帮服务
  node create-order.js --priceToken="abc123xyz" --receiverPhone="13800138000" --note="帮我搬一箱矿泉水到3楼"

注意:
  - priceToken 有时效性，请在询价后尽快创建订单
  - 如账户余额不足，将返回支付链接，用户可点击选择微信/支付宝支付
  - 帮帮订单务必填写 --note 参数描述具体帮帮内容
`);
    process.exit(1);
  }
  
  try {
    const result = await createOrder({
      priceToken: args.priceToken,
      receiverPhone: args.receiverPhone,
      channel: args.channel || '',
      note: args.note || ''
    });
    
    if (result) {
      console.log('📊 创建结果:');
      console.log(JSON.stringify(result, null, 2));
      
      if (result && result.body) {
        const data = result.body;
        // 检查是否需要支付（余额不足）
        if (data.orderUrl) {
          const paymentUrl = data.orderUrl;
          const orderCode = data.orderCode;
          
          // 余额不足，引导第三方支付
          console.log('\n⚠️  账户余额不足，需要完成支付');
          console.log(`   订单编号: ${orderCode}`);
          
          // 检查是否为微信渠道，只有微信渠道才生成二维码图片
          const isWechatChannel = args.channel && args.channel.toLowerCase() === 'wechat';
          
          if (isWechatChannel) {
            // 微信渠道：生成二维码图片
            const qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(paymentUrl)}`;
            
            try {
              // 写入用户主目录下的配置目录，skill 安装目录可能只读
              const qrFilePath = path.join(CONFIG_DIR, 'payment_qrcode.png');
              
              const response = await axios.get(qrcodeUrl, { responseType: 'arraybuffer', timeout: 10000 });
              fs.mkdirSync(CONFIG_DIR, { recursive: true });
              fs.writeFileSync(qrFilePath, response.data);
              
              console.log('\n💳 支付信息：');
              console.log(`   支付链接: ${paymentUrl}`);
              console.log(`   二维码图片: ${qrFilePath}`);
              
              // 输出特殊标记，供 Agent 识别
              console.log('\n[PAYMENT_REQUIRED]');
              console.log(`ORDER_CODE=${orderCode}`);
              console.log(`PAYMENT_URL=${paymentUrl}`);
              console.log(`QRCODE_FILE=${qrFilePath}`);
            } catch (downloadErr) {
              console.error('   下载二维码失败:', downloadErr.message);
              
              console.log('\n💳 支付信息：');
              console.log(`   支付链接: ${paymentUrl}`);
              
              console.log('\n[PAYMENT_REQUIRED]');
              console.log(`ORDER_CODE=${orderCode}`);
              console.log(`PAYMENT_URL=${paymentUrl}`);
            }
          } else {
            // 其他渠道：只输出支付链接
            console.log('\n💳 支付信息：');
            console.log(`   支付链接: ${paymentUrl}`);
            
            console.log('\n[PAYMENT_REQUIRED]');
            console.log(`ORDER_CODE=${orderCode}`);
            console.log(`PAYMENT_URL=${paymentUrl}`);
          }
          
          console.log('\n   支付完成后，订单将自动生效');
        } else {
          console.log('\n✅ 订单创建成功!');
          console.log(`   订单编号: ${data.orderCode}`);
          console.log('\n💡 提示: 使用订单编号可查询订单详情或跟踪跑男位置');
        }
      }
    }
  } catch (error) {
    console.error('执行失败:', error.message);
    process.exit(1);
  }
}

main();
