#!/usr/bin/env node

/**
 * 订单询价脚本
 * 用法: node order-price.js --fromAddress="起始地址" --toAddress="目的地址" [--cityName="城市名"] [--orderType="send|help"]
 */

const { orderPrice, formatPrice } = require('../index');

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
  
  if (!args.fromAddress || !args.toAddress) {
    console.log(`
🚚 订单询价

用法:
  node order-price.js --fromAddress="起始地址" --toAddress="目的地址" [--cityName="城市名"] [--orderType="send|help"]

参数:
  --fromAddress  起始地址（必填，要求完整地址信息。帮帮订单时填写帮帮地点）
  --toAddress    目的地址（必填，要求完整地址信息。帮帮订单时与fromAddress相同）
  --cityName     城市名称（可选，默认郑州市，需要带"市"字）
  --orderType    订单类型（可选，send=跑腿配送，help=帮帮服务，默认send）

示例:
  # 跑腿配送询价
  node order-price.js --fromAddress="郑州市金水区农业路经三路交叉口" --toAddress="郑州市二七区德化街100号"
  node order-price.js --fromAddress="北京市朝阳区三里屯" --toAddress="北京市海淀区中关村" --cityName="北京市"
  # 帮帮服务询价
  node order-price.js --fromAddress="郑州市金水区农业路经三路交叉口" --orderType="help"
`);
    process.exit(1);
  }
  
  try {
    const result = await orderPrice({
      fromAddress: args.fromAddress,
      toAddress: args.toAddress,
      cityName: args.cityName,
      orderType: args.orderType
    });
    
    if (result) {
      console.log('📊 询价结果:');
      console.log(JSON.stringify(result, null, 2));
      
      // 如果有价格信息，格式化显示
      if (result.body) {
        console.log('\n💰 价格摘要:');
        // 优先使用 needPayMoney，其次使用 totalMoney
        const price = result.body.needPayMoney !== undefined ? result.body.needPayMoney : (result.body.totalMoney || 0);
        console.log(`   预估费用: ${formatPrice(price)} 元`);
        if (result.body.distance) {
          console.log(`   配送距离: ${(result.body.distance / 1000).toFixed(2)} 公里`);
        }
        if (result.body.priceToken) {
          console.log(`   priceToken: ${result.body.priceToken}`);
          console.log('\n💡 提示: 使用此 priceToken 创建订单');
        }
      }
    }
  } catch (error) {
    console.error('执行失败:', error.message);
    process.exit(1);
  }
}

main();
