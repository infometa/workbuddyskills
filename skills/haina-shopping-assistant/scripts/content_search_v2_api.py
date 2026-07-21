"""
内容搜索V2 API
"""

import os
from typing import Dict, List
import time
import requests


class ContentSearchV2API:
    
    def __init__(self):
        """
        初始化 API 客户端
        """
        self.api_url = "https://gw-openapi.zhidemai.com/content_search_rank/v1/search"
        self.x_api_key = os.getenv("ZHIDEMAI_CONTENT_SEARCH", "ebdc47644d7c8fb74491cb1021f98c3a")  # 需要申请【内容搜索V2】的 Key 进行配置，现在配置的是【腾讯WorkBuddy】Skill 的体验 Key
        if not self.x_api_key:
            raise ValueError("缺少内容搜索 API 的凭证配置，请联系值得买官方邮件 group-content@zhidemai.com 申请接入 Key，或检查环境变量是否成功配置。")
        
    def search(self, query: str, question_id: str, query_rewrite: bool, correlate_enhance: bool, return_size: int, request_from: str, start_time: str,data_source: List[str]) -> Dict:
        """
        执行内容搜索
        
        Args:
            query: 搜索查询
            question_id: 问题ID
            query_rewrite: 是否进行 query 改写
            correlate_enhance: 是否关联增强
            return_size: 返回数量
            request_from: 请求来源
            start_time: 开始时间
            data_source: 数据源列表
        
        Returns:
            搜索结果字典
        """
        request_data = {
            "query": query,
            "question_id": question_id,
            "query_rewrite": query_rewrite,
            "correlate_enhance": correlate_enhance,
            "return_size": return_size,
            "request_from": request_from,
            "start_time": start_time,
            "data_source": data_source
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.x_api_key
                },
                json=request_data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            content_list = result.get("data", {}).get("content_list", [])
            print(f"内容搜索成功: query={query}, 返回{len(content_list)}条结果")
            return result
        
        except Exception as e:
            print(f"内容搜索 API 调用失败: {str(e)}")
            return {"error_code": -1, "error_msg": str(e), "data": {"content_list": []}}
    
    def extract_articles(self, search_result: Dict) -> List[Dict]:
        """
        从搜索结果中提取文章信息
        根据 API response 格式，只保留核心字段
        
        Args:
            search_result: 搜索结果
        
        Returns:
            文章信息列表
        """
        articles = []
        
        # 检查错误码
        if search_result.get("error_code") != 0:
            print(f"搜索结果包含错误: {search_result.get('error_msg', 'Unknown error')}")
            return articles
        
        content_list = search_result.get("data", {}).get("content_list", [])
        
        for item in content_list:
            # 只保留 API response 中实际返回的核心字段
            article = {
                'title': item.get('works_title', ''),
                'context': item.get('works_content', ''),
                'article_link': item.get('works_link', ''),
                'source': item.get('website_cname', ''),
                'publish_time': item.get('works_pub_time', ''),
                'type': item.get('works_type', 'article')
            }
            articles.append(article)
        
        return articles


def main():
    """测试函数"""
    query = "软壳选购指南｜凯乐石M8系列怎么选"
    start_time = time.time()
    
    content_search_v2 = ContentSearchV2API()
    result = content_search_v2.search(
        query=query,
        question_id="1",
        query_rewrite=False,
        correlate_enhance=True,
        return_size=20,
        request_from="skills",
        start_time="",
        data_source=[]
    )
    
    end_time = time.time()
    print(f"返回结果数: {len(result.get('data', {}).get('content_list', []))}")
    print(f"耗时: {end_time - start_time:.2f}秒")
    
    # 提取文章
    articles = content_search_v2.extract_articles(result)
    print(f"提取文章数: {len(articles)}")


if __name__ == "__main__":
    main()
