"""
搜索 API 并发执行
根据意图类型执行对应的搜索
"""

import sys
import json
import time
import concurrent.futures
from typing import Dict, List, Tuple
from product_search_pro_api import ProductSearchProAPI
from content_search_v2_api import ContentSearchV2API

# 创建 API 实例
product_api = ProductSearchProAPI()
content_api = ContentSearchV2API()

DEFAULT_QUESTION_ID = "1"
DEFAULT_REQUEST_FROM = "skills"
DEFAULT_QUERY_PROCESS = 1
DEFAULT_PRODUCT_SIZE = 5
DEFAULT_CONTENT_SIZE = 5
MAX_WORKERS = 10


def search_single_product(api: ProductSearchProAPI, product_query: str, size: int) -> Tuple[str, Dict]:
    """
    执行单个商品搜索
    
    Args:
        api: ProductSearchProAPI实例
        product_query: 商品搜索词
        size: 返回数量
        
    Returns:
        (商品搜索词, 搜索结果)
    """
    result = api.search(
        product_query=product_query,
        question_id=DEFAULT_QUESTION_ID,
        request_from=DEFAULT_REQUEST_FROM,
        query_process=DEFAULT_QUERY_PROCESS,
        size=size,
        mall_id="",
        brand_name="",
        category_name="",
        min_price=None,
        max_price=None,
        sort="",
        fields=""
    )
    return (product_query, result)


def search_single_content(api: ContentSearchV2API, content_query: str, size: int) -> Tuple[str, Dict]:
    """
    执行单个内容搜索
    
    Args:
        api: ContentSearchV2API实例
        content_query: 内容搜索词
        size: 返回数量
        
    Returns:
        (内容搜索词, 搜索结果)
    """
    result = api.search(
        query=content_query,
        question_id=DEFAULT_QUESTION_ID,
        query_rewrite=False,
        correlate_enhance=True,
        return_size=size,
        request_from=DEFAULT_REQUEST_FROM,
        start_time="",
        data_source=[]
    )
    return (content_query, result)


def multi_search(user_query: str, intent: str, product_queries: List[str] = None, content_queries: List[str] = None, product_size: int = DEFAULT_PRODUCT_SIZE, content_size: int = DEFAULT_CONTENT_SIZE) -> Dict:
    """
    执行智能搜索，根据意图类型执行对应搜索
    
    Args:
        intent: 用户意图（商品总结/商品推荐/商品对比/优惠好价）
        user_query: 用户原始查询
        product_queries: 商品搜索词列表（优惠好价使用）
        content_queries: 内容搜索词列表（商品推荐/总结/对比使用）
        product_size: 每个商品搜索返回数量
        content_size: 每个内容搜索返回数量
        
    Returns:
        包含所有搜索结果的字典
    """
    # 至少需要提供一种搜索词
    if not product_queries and not content_queries:
        raise ValueError("必须提供商品搜索词或内容搜索词")

    start_time = time.time()
    
    # 使用线程池并发执行所有搜索任务
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_query = {}
        
        # 提交商品搜索任务
        if product_queries and product_api:
            for pq in product_queries:
                future = executor.submit(search_single_product, product_api, pq, product_size)
                future_to_query[future] = ('product', pq)
        
        # 提交内容搜索任务
        if content_queries and content_api:
            for cq in content_queries:
                future = executor.submit(search_single_content, content_api, cq, content_size)
                future_to_query[future] = ('content', cq)
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_query):
            query_type, query = future_to_query[future]
            try:
                result_tuple = future.result()  # 返回 (query, result)
                actual_result = result_tuple[1]  # 提取实际的搜索结果
                all_results.append((query_type, query, actual_result))
            except Exception as e:
                print(f"搜索失败: {query} - {str(e)}")
                error_result = {"error_code": -1, "error_msg": str(e), "data": {"rows": []} if query_type == 'product' else {"content_list": []}}
                all_results.append((query_type, query, error_result))
    
    end_time = time.time()
    
    # 分离商品搜索结果和内容搜索结果
    product_results = [(r[1], r[2]) for r in all_results if r[0] == 'product']
    content_results = [(r[1], r[2]) for r in all_results if r[0] == 'content']
    
    # 提取并整合结果
    all_products = {}
    if product_api and product_results:
        for product_query, result in product_results:
            products = product_api.extract_products(result)
            all_products[product_query] = products
    
    all_articles = {}
    if content_api and content_results:
        for content_query, result in content_results:
            articles = content_api.extract_articles(result)
            all_articles[content_query] = articles
    
    # 计算总数
    total_products = sum(len(products) for products in all_products.values())
    total_articles = sum(len(articles) for articles in all_articles.values())
    
    return {
        "intent": intent,
        "user_query": user_query,
        "product_queries": product_queries or [],
        "content_queries": content_queries or [],
        "product_count": total_products,
        "content_count": total_articles,
        "duration": f"{end_time - start_time:.2f}秒",
        "products_by_query": all_products,
        "articles_by_query": all_articles,
    }


def main():
    """
    命令行入口
    
    使用方法:
        python search_work_main.py --user_query "用户原始查询" --intent "商品总结" --content_query '["内容1", "内容2"]' --content_size 5
    
    示例:
        # 商品总结
        python search_work_main.py --user_query "iPhone 16怎么样" --intent "商品总结" --content_query '["iPhone 16 评测", "iPhone 16 使用体验"]'
        
        # 商品推荐
        python search_work_main.py --user_query "推荐一款游戏本" --intent "商品推荐" --content_query '["游戏本 选购指南", "游戏本 推荐"]'
        
        # 商品对比
        python search_work_main.py --user_query "iPhone 16和小米14怎么选" --intent "商品对比" --product_query '["iPhone 16", "小米14"]' --content_query '["iPhone 16对比小米14", "手机横评"]'
        
        # 优惠好价
        python search_work_main.py --user_query "iPhone 16哪里买便宜" --intent "优惠好价" --product_query '["iPhone 16"]' --product_size 5
    """
    
    intent = None
    user_query = None
    product_queries = None
    content_queries = None
    product_size = DEFAULT_PRODUCT_SIZE
    content_size = DEFAULT_CONTENT_SIZE
    
    # 解析参数
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--user_query':
            if i + 1 >= len(sys.argv):
                print("错误：--user_query 缺少参数值")
                sys.exit(1)
            user_query = sys.argv[i + 1]
            i += 2
        
        elif sys.argv[i] == '--intent':
            if i + 1 >= len(sys.argv):
                print("错误：--intent 缺少参数值")
                sys.exit(1)
            intent = sys.argv[i + 1]
            if intent not in ["商品推荐", "商品总结", "商品对比", "优惠好价"]:
                print(f"错误：不支持的意图类型 '{intent}'")
                print("支持的意图：商品推荐、商品总结、商品对比、优惠好价")
                sys.exit(1)
            i += 2
        
        elif sys.argv[i] == '--product_query':
            if i + 1 >= len(sys.argv):
                print("错误：--product_query 缺少参数值")
                sys.exit(1)
            try:
                product_queries = json.loads(sys.argv[i + 1])
                if not isinstance(product_queries, list):
                    raise ValueError("product_query 必须是数组格式")
                i += 2
            except (json.JSONDecodeError, ValueError) as e:
                print(f"错误：无法解析商品搜索词 - {e}")
                sys.exit(1)
        
        elif sys.argv[i] == '--content_query':
            if i + 1 >= len(sys.argv):
                print("错误：--content_query 缺少参数值")
                sys.exit(1)
            try:
                content_queries = json.loads(sys.argv[i + 1])
                if not isinstance(content_queries, list):
                    raise ValueError("content_query 必须是数组格式")
                i += 2
            except (json.JSONDecodeError, ValueError) as e:
                print(f"错误：无法解析内容搜索词 - {e}")
                sys.exit(1)
        
        elif sys.argv[i] == '--product_size':
            if i + 1 >= len(sys.argv):
                print("错误：--product_size 缺少参数值")
                sys.exit(1)
            try:
                product_size = int(sys.argv[i + 1])
                if product_size <= 0:
                    raise ValueError("product_size 必须大于 0")
                i += 2
            except ValueError as e:
                print(f"错误：无法解析商品搜索返回数量 - {e}")
                sys.exit(1)
        
        elif sys.argv[i] == '--content_size':
            if i + 1 >= len(sys.argv):
                print("错误：--content_size 缺少参数值")
                sys.exit(1)
            try:
                content_size = int(sys.argv[i + 1])
                if content_size <= 0:
                    raise ValueError("content_size 必须大于 0")
                i += 2
            except ValueError as e:
                print(f"错误：无法解析内容搜索返回数量 - {e}")
                sys.exit(1)
        
        else:
            print(f"错误：未知的参数 '{sys.argv[i]}'")
            print("支持的参数：--user_query, --intent, --product_query, --content_query, --product_size, --content_size")
            sys.exit(1)
    
    # 验证必要参数
    if not user_query:
        print("错误：缺少 --user_query 参数")
        sys.exit(1)
    if not intent:
        print("错误：缺少 --intent 参数")
        sys.exit(1)
    if not product_queries and not content_queries:
        print("错误：必须提供 --product_query 或 --content_query 参数")
        sys.exit(1)
    
    # 执行搜索
    print(f"用户查询：{user_query}")
    print(f"执行模式：{intent}")
    if product_queries:
        print(f"商品搜索词：{', '.join(product_queries)}")
    if content_queries:
        print(f"内容搜索词：{', '.join(content_queries)}")
        
    result = multi_search(user_query, intent, product_queries, content_queries, product_size=product_size, content_size=content_size)
    
    print(f"\n搜索完成！")
    if result['product_queries']:
        print(f"商品搜索：共找到 {result['product_count']} 个商品")
    if result['content_queries']:
        print(f"内容搜索：共找到 {result['content_count']} 篇文章")
    print(f"总耗时：{result['duration']}")
    
    # 输出 JSON 结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
