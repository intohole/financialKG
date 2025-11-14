#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金融知识图谱系统 - 新闻爬虫模块

负责从金融新闻网站抓取内容，支持多源并发爬取和智能正文提取。
采用异步编程设计，确保高效性和稳定性。
"""

import asyncio
import hashlib
import logging
import re
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import aiofiles


logger = logging.getLogger(__name__)


class NewsCrawler:
    """新闻爬虫 - 异步实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置
        """
        self.config = config
        self.source_urls = config.get('source_urls', [])
        self.max_concurrent = config.get('max_concurrent', 5)
        self.timeout = config.get('timeout', 30)
        self.user_agent = config.get('user_agent', 
                                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        # 限制爬取速率
        self.request_delay = 1.0  # 请求间隔（秒）
        self.last_request_time = 0
        
        # 预编译正则表达式
        self.content_patterns = [
            re.compile(r'<article[^>]*>(.*?)</article>', re.DOTALL | re.IGNORECASE),
            re.compile(r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>', re.DOTALL | re.IGNORECASE),
            re.compile(r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>', re.DOTALL | re.IGNORECASE),
            re.compile(r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>', re.DOTALL | re.IGNORECASE),
            re.compile(r'<main[^>]*>(.*?)</main>', re.DOTALL | re.IGNORECASE),
        ]
        
        self.title_patterns = [
            re.compile(r'<h1[^>]*>(.*?)</h1>', re.DOTALL | re.IGNORECASE),
            re.compile(r'<title[^>]*>(.*?)</title>', re.DOTALL | re.IGNORECASE),
        ]
        
        # 清理标签
        self.cleanup_tags = ['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']
    
    async def _rate_limit(self) -> None:
        """请求速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        parsed = urlparse(url)
        return parsed.netloc
    
    def _is_valid_url(self, url: str) -> bool:
        """检查URL是否有效"""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc]) and parsed.scheme in ['http', 'https']
        except:
            return False
    
    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _clean_html(self, html: str) -> str:
        """清理HTML内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除指定的标签
        for tag in self.cleanup_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # 移除空白字符
        for tag in soup.find_all():
            if tag.string:
                tag.string = ' '.join(tag.string.split())
        
        return str(soup)
    
    def _extract_main_content(self, html: str) -> Tuple[str, str]:
        """提取主要内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试多种模式提取标题
        title = ""
        for pattern in self.title_patterns:
            match = pattern.search(html)
            if match:
                title_text = BeautifulSoup(match.group(1), 'html.parser').get_text()
                title = title_text.strip()
                break
        
        if not title:
            # 备选方案：从title标签获取
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
        
        # 尝试多种模式提取正文
        content = ""
        
        for pattern in self.content_patterns:
            match = pattern.search(html)
            if match:
                content_html = match.group(1)
                # 清理HTML
                cleaned_content = self._clean_html(content_html)
                content_soup = BeautifulSoup(cleaned_content, 'html.parser')
                content_text = content_soup.get_text().strip()
                
                if len(content_text) > 100:  # 至少100字符
                    content = content_text
                    break
        
        if not content:
            # 备选方案：提取所有段落
            paragraphs = soup.find_all('p')
            if paragraphs:
                content_parts = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_parts.append(text)
                content = '\n\n'.join(content_parts)
        
        return title, content
    
    def _filter_financial_content(self, url: str, title: str, content: str) -> bool:
        """过滤金融相关内容"""
        # 如果内容太少，跳过
        if len(content) < 200:
            return False
        
        # 金融相关关键词
        financial_keywords = [
            '股票', '股市', '证券', '基金', '期货', '银行', '保险',
            '投资', '融资', '上市', 'IPO', '并购', '重组', '分红',
            '财报', '业绩', '利润', '收入', '股价', '市值',
            '人民币', '汇率', '利率', '货币政策', '央行',
            '公司', '企业', '集团', '股份', '有限责任公司',
            '金融', '财经', '商业', '经济', '市场'
        ]
        
        # 组合文本进行检查
        full_text = f"{title} {content}".lower()
        
        # 至少包含一个金融关键词
        has_financial_keyword = any(keyword in full_text for keyword in financial_keywords)
        
        # 排除一些明显不相关的URL
        exclude_patterns = [
            'video', 'video.html', 'live', 'forum', 'bbs',
            'about', 'contact', 'privacy', 'terms'
        ]
        
        has_exclude_pattern = any(pattern in url.lower() for pattern in exclude_patterns)
        
        return has_financial_keyword and not has_exclude_pattern
    
    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
        """获取单个页面内容"""
        try:
            await self._rate_limit()
            
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = await client.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            html = response.text
            title, content = self._extract_main_content(html)
            
            # 过滤金融相关内容
            if not self._filter_financial_content(url, title, content):
                logger.debug(f"内容不符合金融主题，跳过: {url}")
                return None
            
            # 生成内容哈希
            content_hash = self._generate_content_hash(content)
            
            result = {
                'url': url,
                'title': title,
                'content': content,
                'content_hash': content_hash,
                'fetch_time': datetime.now(),
                'domain': self._extract_domain(url),
                'status': 'success'
            }
            
            logger.info(f"页面抓取成功: {url} (标题: {title[:50]}...)")
            return result
            
        except httpx.TimeoutException:
            logger.warning(f"请求超时: {url}")
            return {'url': url, 'status': 'timeout'}
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP错误 {e.response.status_code}: {url}")
            return {'url': url, 'status': 'http_error', 'error': str(e)}
        except Exception as e:
            logger.error(f"抓取页面失败: {url}, 错误: {e}")
            return {'url': url, 'status': 'error', 'error': str(e)}
    
    async def _discover_urls(self, client: httpx.AsyncClient, 
                           base_url: str) -> List[str]:
        """发现新闻链接"""
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = await client.get(base_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找可能的新闻链接
            news_urls = []
            
            # 查找常见的新闻链接选择器
            link_selectors = [
                'a[href*="/news/"]',
                'a[href*="/article/"]',
                'a[href*="/story/"]',
                'a[href*="/content/"]',
                'a[href*="news"]',
                'a[href*="article"]',
                'a[href*="story"]',
                'a[class*="news"]',
                'a[class*="article"]',
                'a[class*="story"]',
                'h2 a',
                'h3 a',
                'h4 a'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        # 转换为绝对URL
                        full_url = urljoin(base_url, href)
                        
                        # 验证URL有效性
                        if self._is_valid_url(full_url):
                            # 避免重复
                            if full_url not in news_urls:
                                news_urls.append(full_url)
            
            # 去重并限制数量
            unique_urls = list(set(news_urls))[:50]  # 最多50个链接
            
            logger.info(f"从 {base_url} 发现 {len(unique_urls)} 个新闻链接")
            return unique_urls
            
        except Exception as e:
            logger.error(f"发现链接失败: {base_url}, 错误: {e}")
            return []
    
    async def crawl_source(self, source_url: str, 
                          max_pages: int = 10) -> List[Dict[str, Any]]:
        """爬取单个数据源"""
        logger.info(f"开始爬取数据源: {source_url}")
        
        results = []
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=self.max_concurrent)
        ) as client:
            
            # 首先发现新闻链接
            news_urls = await self._discover_urls(client, source_url)
            
            # 如果没有发现链接，直接爬取主页
            if not news_urls:
                logger.warning(f"未发现新闻链接，尝试爬取主页: {source_url}")
                page_result = await self._fetch_page(client, source_url)
                if page_result and page_result.get('status') == 'success':
                    results.append(page_result)
            else:
                # 并发爬取发现的链接
                semaphore = asyncio.Semaphore(self.max_concurrent)
                
                async def fetch_with_semaphore(url: str):
                    async with semaphore:
                        return await self._fetch_page(client, url)
                
                # 限制爬取数量
                urls_to_crawl = news_urls[:max_pages]
                tasks = [fetch_with_semaphore(url) for url in urls_to_crawl]
                
                page_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 过滤成功的结果
                for result in page_results:
                    if isinstance(result, dict) and result.get('status') == 'success':
                        results.append(result)
        
        logger.info(f"数据源爬取完成: {source_url}, 成功获取 {len(results)} 个页面")
        return results
    
    async def crawl_all_sources(self, max_pages_per_source: int = 10) -> List[Dict[str, Any]]:
        """爬取所有配置的数据源"""
        logger.info(f"开始爬取 {len(self.source_urls)} 个数据源")
        
        all_results = []
        
        # 使用信号量限制总并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def crawl_with_semaphore(source_url: str):
            async with semaphore:
                return await self.crawl_source(source_url, max_pages_per_source)
        
        # 并发爬取所有数据源
        tasks = [crawl_with_semaphore(url) for url in self.source_urls]
        source_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 汇总结果
        for result in source_results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"数据源爬取异常: {result}")
        
        logger.info(f"所有数据源爬取完成，共获取 {len(all_results)} 个有效页面")
        return all_results
    
    async def save_to_file(self, results: List[Dict[str, Any]], 
                          filename: Optional[str] = None) -> str:
        """保存结果到文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/crawled_news_{timestamp}.json"
        
        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            import json
            await f.write(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        
        logger.info(f"结果已保存到: {filename}")
        return filename


class CrawlerManager:
    """爬虫管理器 - 统一接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化爬虫管理器"""
        self.config = config
        self.crawler = NewsCrawler(config)
    
    async def run_crawl(self, save_to_db: bool = True, 
                       max_pages_per_source: int = 10) -> List[Dict[str, Any]]:
        """
        运行爬虫任务
        
        Args:
            save_to_db: 是否保存到数据库
            max_pages_per_source: 每个数据源最大页面数
            
        Returns:
            爬取结果列表
        """
        try:
            # 运行爬虫
            results = await self.crawler.crawl_all_sources(max_pages_per_source)
            
            if save_to_db and results:
                # 保存到数据库
                from database_manager import db_manager
                
                for result in results:
                    try:
                        await db_manager.insert_source_document(result)
                    except Exception as e:
                        logger.error(f"保存文档到数据库失败: {e}")
            
            # 可选：保存到文件
            if results:
                await self.crawler.save_to_file(results)
            
            return results
            
        except Exception as e:
            logger.error(f"爬虫任务执行失败: {e}")
            raise


# 爬虫配置模板
DEFAULT_CRAWLER_CONFIG = {
    'source_urls': [
        'https://finance.sina.com.cn/',
        'https://finance.caijing.com.cn/',
        'https://finance.eastmoney.com/',
    ],
    'max_concurrent': 5,
    'timeout': 30,
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'crawl_interval': 3600,  # 爬取间隔（秒）
}


def create_crawler_manager(config: Optional[Dict[str, Any]] = None) -> CrawlerManager:
    """创建爬虫管理器"""
    if config is None:
        config = DEFAULT_CRAWLER_CONFIG
    return CrawlerManager(config)