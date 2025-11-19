"""
路由基类和通用路由工具
"""

from typing import Any, Generic, List, Optional, TypeVar

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.exception_handlers import (handle_generic_exception,
                                        handle_value_error)
from ..utils.responses import ErrorResponse, SuccessResponse
from .deps import get_db, get_logger

# 全局路由注册表：用于检测跨路由类的重复路由
# 格式：{route_key: (router_instance, route_info)}
# route_key 格式："{method}#{full_path}"
global_route_registry = {}

# 全局重复路由记录：用于追溯删除操作
# 格式：{route_key: [(router_instance, route_info), ...]}
global_duplicate_routes = {}

T = TypeVar("T")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseRouter:
    """
    API路由基类，提供通用的CRUD操作和响应处理
    """

    def __init__(
        self, prefix: str, tags: List[str], dependencies: Optional[List[Any]] = None
    ):
        """
        初始化路由基类

        Args:
            prefix: 路由前缀
            tags: API标签
            dependencies: 路由依赖列表
        """
        self.prefix = prefix
        self.tags = tags
        self.dependencies = dependencies or []
        self.router = APIRouter(
            prefix=prefix, tags=tags, dependencies=self.dependencies
        )
        self.logger = get_logger()

        # 路由注册表：用于检测重复路由
        # 格式：{method: {path: route_info}}
        self.route_registry = {}

        # 重复路由记录：用于追溯删除操作
        # 格式：{method: {path: [original_route, duplicate_route]}}
        self.duplicate_routes = {}

        # 路由初始化标记：确保路由仅注册一次
        self._router_initialized = False

    def _get_route_key(self, method: str, path: str) -> str:
        """
        获取路由的唯一标识键

        Args:
            method: HTTP方法
            path: 路由路径

        Returns:
            str: 路由唯一标识键
        """
        return f"{method}#{path}"

    def _extract_route_info(self, route: Any) -> dict:
        """
        提取路由信息

        Args:
            route: 路由对象

        Returns:
            dict: 路由信息字典
        """
        return {
            "path": route.path,
            "method": route.methods,
            "endpoint": route.endpoint.__name__,  # 获取函数名
            "tags": route.tags,
            "dependencies": route.dependencies,
        }

    def _detect_internal_duplicates(self) -> None:
        """
        检测当前路由类内部的重复路由
        """
        duplicates = {}

        # 遍历当前路由的所有路径
        for route in self.router.routes:
            # 处理有多个HTTP方法的路由
            for method in route.methods:
                if method == "OPTIONS":  # 忽略OPTIONS方法
                    continue

                # 构造完整的路径（route.path已经包含了前缀，无需再次添加）
                full_path = route.path
                route_key = self._get_route_key(method, full_path)
                route_info = self._extract_route_info(route)
                route_info["router_prefix"] = self.prefix
                route_info["router_tags"] = self.tags

                # 检测当前路由类内部的重复路由
                if route_key in self.route_registry:
                    if method not in duplicates:
                        duplicates[method] = {}
                    if full_path not in duplicates[method]:
                        duplicates[method][full_path] = []

                    original_route = self.route_registry[route_key]
                    duplicates[method][full_path].append((original_route, route_info))
                    self.logger.warning(f"[内部] 检测到重复路由：{method} {full_path}")
                    self.logger.warning(f"原始路由：{original_route}")
                    self.logger.warning(f"重复路由：{route_info}")
                else:
                    self.route_registry[route_key] = route_info

        # 保存重复路由记录
        self.duplicate_routes = duplicates

    def _register_routes_to_global(self) -> None:
        """
        将当前路由注册到全局路由注册表
        """
        # 检查路由是否已经注册过
        if self._router_initialized:
            self.logger.debug(f"路由已注册到全局注册表: {self.__class__.__name__}")
            return

        # 遍历当前路由的所有路径
        for route in self.router.routes:
            # 处理有多个HTTP方法的路由
            for method in route.methods:
                if method == "OPTIONS":  # 忽略OPTIONS方法
                    continue

                # 构造完整的路径（route.path已经包含了前缀，无需再次添加）
                full_path = route.path
                route_key = self._get_route_key(method, full_path)
                route_info = self._extract_route_info(route)
                route_info["router_prefix"] = self.prefix
                route_info["router_tags"] = self.tags

                # 检测跨路由类的重复路由
                if route_key in global_route_registry:
                    # 检查当前路由是否来自同一个路由器实例
                    existing_router, existing_route_info = global_route_registry[
                        route_key
                    ]
                    if existing_router == self:
                        # 来自同一个实例，不是重复路由，跳过
                        continue

                    # 来自不同实例，记录为重复路由
                    if route_key not in global_duplicate_routes:
                        global_duplicate_routes[route_key] = []
                        # 添加原始路由到重复记录
                        global_duplicate_routes[route_key].append(
                            global_route_registry[route_key]
                        )

                    global_duplicate_routes[route_key].append((self, route_info))

                    self.logger.warning(f"[全局] 检测到重复路由：{method} {full_path}")
                    self.logger.warning(
                        f"原始路由来自：{existing_router.__class__.__name__}"
                    )
                    self.logger.warning(f"重复路由来自：{self.__class__.__name__}")
                else:
                    # 记录到全局注册表
                    global_route_registry[route_key] = (self, route_info)

        # 标记路由已注册
        self._router_initialized = True

    def _remove_duplicate_routes(self) -> None:
        """
        移除重复路由，只保留第一个注册的路由
        """
        if not self.duplicate_routes and not global_duplicate_routes:
            return

        # 临时存储保留的路由
        kept_routes = []
        seen_routes = set()

        for route in self.router.routes:
            # 处理有多个HTTP方法的路由
            route_methods = list(route.methods)
            is_duplicate = False

            for method in route_methods:
                if method == "OPTIONS":  # 忽略OPTIONS方法
                    continue

                full_path = route.path
                route_key = self._get_route_key(method, full_path)
                global_route_key = self._get_route_key(method, full_path)

                # 检测当前路由类内部的重复路由
                if route_key in seen_routes:
                    is_duplicate = True
                    break

                # 检测跨路由类的重复路由
                if global_route_key in global_duplicate_routes:
                    # 检查当前路由是否是第一个注册的
                    first_router, first_route_info = global_route_registry[
                        global_route_key
                    ]
                    if first_router != self:
                        is_duplicate = True
                        break

                seen_routes.add(route_key)

            if not is_duplicate:
                kept_routes.append(route)
            else:
                self.logger.info(f"已移除重复路由：{list(route.methods)} {route.path}")

        # 计算移除的路由数量
        removed_count = len(self.router.routes) - len(kept_routes)
        if removed_count > 0:
            # 更新路由列表
            self.router.routes = kept_routes
            self.logger.info(f"重复路由移除完成，共移除 {removed_count} 个重复路由")

    def detect_and_remove_duplicates(self) -> dict:
        """
        检测并移除重复路由（公开方法）

        Returns:
            dict: 包含当前路由类重复路由和全局重复路由的记录
        """
        # 重置路由注册表
        self.route_registry.clear()
        self.duplicate_routes.clear()

        # 仅检测当前路由类内部的重复路由
        self._detect_internal_duplicates()

        # 移除内部重复路由
        self._remove_duplicate_routes()

        # 将清理后的路由添加到全局注册表
        self._register_routes_to_global()

        return {
            "internal_duplicates": self.duplicate_routes,
            "global_duplicates": global_duplicate_routes,
        }

    def get_router(self) -> APIRouter:
        """
        获取APIRouter实例

        Returns:
            APIRouter: 配置完成的APIRouter实例
        """
        self.detect_and_remove_duplicates()
        return self.router

    async def handle_response(
        self,
        result: Any,
        message: str = "操作成功",
        success: bool = True,
        code: int = 200,
    ) -> dict:
        """
        统一处理API响应

        Args:
            result: 响应数据
            message: 响应消息
            success: 是否成功
            code: 状态码

        Returns:
            dict: 格式化的响应数据
        """
        if success:
            return SuccessResponse(data=result, message=message).dict()
        else:
            return ErrorResponse(message=message, code=code).dict()

    async def handle_create(
        self,
        db: AsyncSession,
        create_data: CreateSchemaType,
        service_method,
        response_model: Optional[type] = None,
    ) -> Any:
        """
        处理创建操作的通用方法

        Args:
            db: 数据库会话
            create_data: 创建数据
            service_method: 服务层创建方法
            response_model: 响应模型类

        Returns:
            Any: 创建结果
        """
        try:
            result = await service_method(db, create_data)
            # 如果提供了响应模型，进行转换
            if response_model and result:
                result = response_model.from_orm(result)
            return await self.handle_response(result, message="创建成功")
        except ValueError as e:
            raise handle_value_error(e, self.logger)
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "创建")

    async def handle_post(
        self,
        db: AsyncSession,
        item_create,
        service_method,
        response_model: Optional[type] = None,
        **kwargs,
    ) -> Any:
        """
        处理创建对象操作的通用方法

        Args:
            db: 数据库会话
            item_create: 创建数据
            service_method: 服务层创建方法
            response_model: 响应模型类
            **kwargs: 额外参数

        Returns:
            Any: 创建结果
        """
        try:
            # 转换为服务层需要的参数格式
            data_dict = item_create.model_dump(exclude_unset=True)
            # 调用服务层方法创建对象
            result = await service_method(db, **data_dict, **kwargs)
            # 如果提供了响应模型，进行转换
            if response_model and result:
                result = response_model.from_orm(result)
            return await self.handle_response(result, message="创建成功")
        except ValueError as e:
            raise handle_value_error(e, self.logger)
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "创建")

    async def handle_get(
        self,
        db: AsyncSession,
        item_id: str,
        service_method,
        response_model: Optional[type] = None,
    ) -> Any:
        """
        处理获取单个对象操作的通用方法

        Args:
            db: 数据库会话
            item_id: 对象ID
            service_method: 服务层获取方法
            response_model: 响应模型类

        Returns:
            Any: 获取结果
        """
        try:
            result = await service_method(db, item_id)
            if not result:
                raise HTTPException(status_code=404, detail="对象不存在")
            # 如果提供了响应模型，进行转换
            if response_model and result:
                result = response_model.from_orm(result)
            return await self.handle_response(result, message="获取成功")
        except HTTPException:
            raise
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "获取")

    async def handle_list(
        self,
        db: AsyncSession,
        service_method,
        response_model: Optional[type] = None,
        **kwargs,
    ) -> Any:
        """
        处理列表查询操作的通用方法

        Args:
            db: 数据库会话
            service_method: 服务层列表查询方法
            response_model: 响应模型类
            **kwargs: 额外的查询参数

        Returns:
            Any: 查询结果
        """
        try:
            # 记录查询参数
            self.logger.info(f"列表查询请求，参数: {kwargs}")

            # 准备调用参数
            call_kwargs = kwargs.copy()
            page = call_kwargs.pop("page", 1)
            limit = call_kwargs.pop("page_size", call_kwargs.pop("limit", 10))

            # 调用服务方法获取数据 - 仅在方法接受db参数时添加
            import inspect
            sig = inspect.signature(service_method)
            if "db" in sig.parameters and "db" not in call_kwargs:
                call_kwargs["db"] = db

            # Check if service method returns tuple (items, total) for proper pagination
            result = await service_method(**call_kwargs)
            if isinstance(result, tuple):
                items, total = result
            else:
                # Legacy behavior: method returns list
                items = result
                total = len(items) if isinstance(items, list) else 0

            # 处理分页
            paginated_items = items
            
            # If service method returned a tuple, it already implemented pagination
            if not isinstance(result, tuple) and page > 1 and limit > 0 and isinstance(items, list):
                # Service method returned full list, need to paginate in memory
                start = (page - 1) * limit
                end = start + limit
                paginated_items = items[start:end]

            # 转换为响应模型
            response_items = []
            if paginated_items:
                if isinstance(paginated_items, list) and response_model:
                    response_items = [response_model.from_orm(item) for item in paginated_items]
                elif response_model:
                    # 如果是单个对象，直接转换
                    response_items = [response_model.from_orm(paginated_items)]
                    total = 1
                else:
                    response_items = paginated_items

            # 创建分页响应
            from kg.api import schemas
            pagination_response = schemas.PaginationResponse(
                items=response_items,
                total=total,
                page=page,
                size=limit
            )

            self.logger.info(
                f"列表查询成功，返回 {len(response_items) if isinstance(response_items, list) else 1} 条数据，总条数: {total}"
            )
            return await self.handle_response(pagination_response, message="查询成功")
        except Exception as e:
            self.logger.error(f"列表查询失败: {str(e)}")
            raise handle_generic_exception(e, self.logger, "查询")

    async def handle_update(
        self,
        db: AsyncSession,
        item_id: str,
        update_data: UpdateSchemaType,
        service_method,
        response_model: Optional[type] = None,
    ) -> Any:
        """
        处理更新操作的通用方法

        Args:
            db: 数据库会话
            item_id: 对象ID
            update_data: 更新数据
            service_method: 服务层更新方法
            response_model: 响应模型类

        Returns:
            Any: 更新结果
        """
        try:
            result = await service_method(db, item_id, update_data)
            if not result:
                raise HTTPException(status_code=404, detail="对象不存在")
            # 如果提供了响应模型，进行转换
            if response_model and result:
                result = response_model.from_orm(result)
            return await self.handle_response(result, message="更新成功")
        except HTTPException:
            raise
        except ValueError as e:
            raise handle_value_error(e, self.logger)
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "更新")

    async def handle_delete(
        self, db: AsyncSession, item_id: str, service_method
    ) -> Any:
        """
        处理删除操作的通用方法

        Args:
            db: 数据库会话
            item_id: 对象ID
            service_method: 服务层删除方法

        Returns:
            Any: 删除结果
        """
        try:
            result = await service_method(db, item_id)
            if not result:
                raise HTTPException(status_code=404, detail="对象不存在")
            return await self.handle_response(None, message="删除成功")
        except HTTPException:
            raise
        except Exception as e:
            raise handle_generic_exception(e, self.logger, "删除")


def detect_global_duplicate_routes() -> dict:
    """
    检测全局范围内的重复路由

    Returns:
        dict: 全局重复路由记录
    """
    logger = get_logger()
    duplicates = {}

    # 遍历全局路由注册表，查找重复路由
    for route_key, route_data in global_route_registry.items():
        if route_key in global_duplicate_routes:
            duplicates[route_key] = global_duplicate_routes[route_key]
            logger.warning(f"[全局检测] 重复路由：{route_key}")
            for router_instance, route_info in global_duplicate_routes[route_key]:
                logger.warning(f"  路由来源：{router_instance.__class__.__name__}")
                logger.warning(f"  路由信息：{route_info}")

    return duplicates


def remove_global_duplicate_routes() -> int:
    """
    移除全局范围内的重复路由，只保留第一个注册的路由

    Returns:
        int: 移除的路由数量
    """
    logger = get_logger()
    removed_count = 0

    # 遍历全局重复路由记录
    for route_key, routes in global_duplicate_routes.items():
        if len(routes) < 2:
            continue

        # 保留第一个路由，移除其他路由
        first_router, first_route = routes[0]
        duplicate_routes = routes[1:]

        # 移除重复路由
        for router_instance, route_info in duplicate_routes:
            # 遍历路由实例的所有路由
            for i, route in enumerate(router_instance.router.routes):
                # 比较路径和方法是否匹配
                full_path = f"{router_instance.prefix}{route.path}"
                for method in route.methods:
                    if method == "OPTIONS":
                        continue

                    current_key = f"{method}#{full_path}"
                    if current_key == route_key:
                        # 移除该路由
                        router_instance.router.routes.pop(i)
                        removed_count += 1
                        logger.info(f"[全局移除] 已移除重复路由：{method} {full_path}")
                        logger.info(
                            f"  移除路由来自：{router_instance.__class__.__name__}"
                        )
                        logger.info(
                            f"  保留路由来自：{first_router.__class__.__name__}"
                        )
                        break

    return removed_count


def reset_global_route_registry() -> None:
    """
    重置全局路由注册表，用于测试或重新注册路由
    """
    global_route_registry.clear()
    global_duplicate_routes.clear()


def detect_and_remove_all_duplicate_routes() -> dict:
    """
    检测并移除全局范围内的所有重复路由

    Returns:
        dict: 移除结果
    """
    logger = get_logger()
    logger.info("开始全局重复路由检测和移除...")

    # 检测全局重复路由
    duplicates = detect_global_duplicate_routes()

    # 移除重复路由
    removed_count = remove_global_duplicate_routes()

    logger.info(
        f"全局重复路由检测和移除完成。共移除 {removed_count} 个重复路由，检测到 {len(duplicates)} 组重复路由"
    )

    return {"duplicates_detected": duplicates, "routes_removed": removed_count}
