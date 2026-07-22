#!/usr/bin/env node

/**
 * 查询订单详情脚本
 * 用法: node order-detail.js --orderCode="订单编号"
 */

const { orderDetail, formatPrice } = require('../index');

// 订单状态码映射
function getOrderStatusText(state) {
  const statusMap = {
    1: '下单成功',
    3: '跑男已接单',
    4: '跑男已到达',
    5: '跑男已取件',
    6: '跑男送达中',
    10: '已完成',
    11: '已取消',
    20: '异常订单'
  };
  return statusMap[state] || `未知状态(${state})`;
}

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
  
  if (!args.orderCode) {
    console.log(`
📋 查询订单详情

用法:
  node order-detail.js --orderCode="订单编号"

参数:
  --orderCode  订单编号（必填）

示例:
  node order-detail.js --orderCode="UU123456789"
`);
    process.exit(1);
  }
  
  try {
    const result = await orderDetail({
      orderCode: args.orderCode
    });
    
    if (result) {
      console.log('📊 订单详情:');
      console.log(JSON.stringify(result, null, 2));
      
      if (result.body) {
        const data = result.body;
        console.log('\n📋 订单摘要:');
        console.log(`   订单编号: ${data.orderCode || args.orderCode}`);
        console.log(`   订单状态: ${getOrderStatusText(data.state)}`);
        if (data.orderPrice) {
          console.log(`   配送费用: ${formatPrice(data.orderPrice)} 元`);
        }
        if (data.fromAddress) {
          console.log(`   起点地址: ${data.fromAddress}`);
        }
        if (data.toAddress) {
          console.log(`   终点地址: ${data.toAddress}`);
        }
        if (data.driverName) {
          console.log(`   跑男姓名: ${data.driverName}`);
          console.log(`   跑男电话: ${data.driverMobile || '-'}`);
        }
      }
    }
  } catch (error) {
    console.error('执行失败:', error.message);
    process.exit(1);
  }
}

main();
