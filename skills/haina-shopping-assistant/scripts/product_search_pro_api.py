"""
商品搜索 API
"""

import os
from typing import Dict, List, Optional
import time
import requests


class ProductSearchProAPI:
    
    def __init__(self):
        """
        初始化 API 客户端
        """
        self.api_url = "https://gw-openapi.zhidemai.com/product/v1"
        self.x_api_key = os.getenv("ZHIDEMAI_PRODUCT_SEARCH", "ebdc47644d7c8fb74491cb1021f98c3a") # 需要申请【商品搜索Pro】的 Key 进行配置，现在配置的是【腾讯WorkBuddy】Skill 的体验 Key
        if not self.x_api_key:
            raise ValueError("缺少商品搜索 Pro 的 API 凭证配置，请联系值得买官方邮件 group-content@zhidemai.com 申请接入 Key，或检查环境变量是否成功配置。")
    
    def search(self, product_query: str, question_id: str,
    request_from: str, query_process: int, size: int, mall_id: str,
    brand_name: str, category_name: str, min_price: Optional[float],
    max_price: Optional[float], sort: str, fields: str) -> Dict:
        """
        执行商品搜索
        
        Args:
            product_query: 商品查询
            question_id: 问题ID
            request_from: 请求来源
            query_process: 查询处理方式
            size: 返回数量
            mall_id: 商城ID
            brand_name: 品牌名称
            category_name: 分类名称
            min_price: 最低价格
            max_price: 最高价格
            sort: 排序方式
            fields: 返回字段
        
        Returns:
            搜索结果字典
        """
        request_data = {
            "request_from": request_from,
            "question_id": question_id,
            "product_query": product_query,
            "query_process": query_process,
            "size": size,
            "mall_id": mall_id,
            "brand_name": brand_name,
            "category_name": category_name,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort,
            "fields": fields
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key": self.x_api_key
                },
                json=request_data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
                
            # 检查错误码
            if result.get("error_code") != 0:
                print(f"商品搜索 API 返回错误: {result.get('error_msg', 'Unknown error')}")
                return {"error_code": result.get("error_code"), "data": {"rows": []}}
            
            rows = result.get("data", {}).get("rows", [])
            print(f"商品搜索成功: query={product_query}, 返回{len(rows)}条结果")
            return result
        
        except Exception as e:
            print(f"商品搜索 API 调用失败: {str(e)}")
            return {"error_code": -1, "error_msg": str(e), "data": {"rows": []}}
    
    def extract_products(self, search_result: Dict) -> List[Dict]:
        """
        从搜索结果中提取商品信息
        根据 API response 格式，只保留核心字段
        
        Args:
            search_result: 搜索结果
        
        Returns:
            商品信息列表
        """
        products = []
        
        if search_result.get("error_code") != 0:
            return products
        
        rows = search_result.get("data", {}).get("rows", [])
        
        for item in rows:
            # 只保留 API response 中实际返回的核心字段
            product = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "main_picture": item.get("main_picture", ""),
                "page_price": item.get("page_price", 0.0),
                "price": item.get("price", ""),
                "mall_name": item.get("mall_name", ""),
                "brand_name": item.get("brand_name", ""),
                "cate1_name": item.get("cate1_name", ""),
                "cate2_name": item.get("cate2_name", ""),
                "cate3_name": item.get("cate3_name", "")
            }
            products.append(product)
        
        return products


def main():
    """测试函数"""
    product_query = "iphone16"
    question_id = "1"
    
    start_time = time.time()
    product_search_pro_api = ProductSearchProAPI()
    result = product_search_pro_api.search(
        product_query=product_query,
        question_id=question_id,
        request_from="skills",
        query_process=1,
        size=20,
        mall_id="",
        brand_name="",
        category_name="",
        min_price=None,
        max_price=None,
        sort="",
        fields=""
    )
    end_time = time.time()
    
    print(f"返回结果数: {len(result.get('data', {}).get('rows', []))}")
    print(f"耗时: {end_time - start_time:.2f}秒")
    
    # 提取商品信息
    products = product_search_pro_api.extract_products(result)
    print(f"\n提取商品数: {len(products)}")


if __name__ == "__main__":
    main()
