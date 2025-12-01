"""
向量数据库服务抽象层
支持多种向量数据库（ChromaDB、Milvus等），便于灵活切换
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VectorDBConfig:
    """向量数据库配置"""
    # 从config模块导入默认配置
    from config import (
        VECTOR_DB_PROVIDER, RAG_COLLECTION_NAME, RAG_DB_PATH,
        MILVUS_HOST, MILVUS_PORT, MILVUS_USER, MILVUS_PASSWORD, MILVUS_DATABASE
    )
    
    provider: str = VECTOR_DB_PROVIDER  # chromadb, milvus
    collection_name: str = RAG_COLLECTION_NAME
    db_path: str = RAG_DB_PATH  # ChromaDB持久化路径，或Milvus的数据库名
    
    # Milvus 配置
    milvus_host: str = MILVUS_HOST
    milvus_port: int = MILVUS_PORT
    milvus_user: Optional[str] = MILVUS_USER
    milvus_password: Optional[str] = MILVUS_PASSWORD
    milvus_database: Optional[str] = MILVUS_DATABASE


class VectorDBService(ABC):
    """向量数据库服务抽象基类"""
    
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化向量数据库服务"""
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, embedding_dimension: int) -> bool:
        """
        创建集合
        
        Args:
            collection_name: 集合名称
            embedding_dimension: 嵌入向量维度
        """
        pass
    
    @abstractmethod
    def get_collection_count(self, collection_name: str) -> int:
        """获取集合中的文档数量"""
        pass
    
    @abstractmethod
    def add_documents(
        self, 
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """
        添加文档到集合
        
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            embeddings: 嵌入向量列表
            documents: 文档内容列表
            metadatas: 元数据列表
        """
        pass
    
    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int
    ) -> Dict[str, Any]:
        """
        搜索相似文档
        
        Args:
            collection_name: 集合名称
            query_embeddings: 查询嵌入向量列表
            n_results: 返回结果数量
            
        Returns:
            包含 documents, metadatas, distances 的字典
            格式: {
                'documents': [[doc1, doc2, ...], ...],
                'metadatas': [[meta1, meta2, ...], ...],
                'distances': [[dist1, dist2, ...], ...]
            }
        """
        pass
    
    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self._initialized


class ChromaDBVectorDBService(VectorDBService):
    """ChromaDB 向量数据库服务实现"""
    
    def __init__(self, config: VectorDBConfig):
        super().__init__(config)
        self.client = None
    
    def initialize(self) -> bool:
        """初始化ChromaDB客户端"""
        try:
            import chromadb
            import os
            
            db_path = self.config.db_path
            os.makedirs(db_path, exist_ok=True)
            logger.info(f"初始化ChromaDB持久化存储，路径: {db_path}")
            self.client = chromadb.PersistentClient(path=db_path)
            
            self._initialized = True
            logger.info("✅ ChromaDB服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化ChromaDB服务失败: {e}")
            self._initialized = False
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        if not self._initialized:
            return False
        try:
            existing_collections = [col.name for col in self.client.list_collections()]
            return collection_name in existing_collections
        except Exception as e:
            logger.error(f"检查集合是否存在失败: {e}")
            return False
    
    def create_collection(self, collection_name: str, embedding_dimension: int) -> bool:
        """创建集合"""
        if not self._initialized:
            return False
        try:
            if self.collection_exists(collection_name):
                logger.info(f"集合 {collection_name} 已存在")
                return True
            self.client.create_collection(name=collection_name)
            logger.info(f"✅ 创建集合: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False
    
    def get_collection_count(self, collection_name: str) -> int:
        """获取集合中的文档数量"""
        if not self._initialized:
            return 0
        try:
            collection = self.client.get_collection(name=collection_name)
            return collection.count()
        except Exception as e:
            logger.error(f"获取集合文档数量失败: {e}")
            return 0
    
    def add_documents(
        self, 
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """添加文档到集合"""
        if not self._initialized:
            return False
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def search(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int
    ) -> Dict[str, Any]:
        """搜索相似文档"""
        if not self._initialized:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}


class MilvusVectorDBService(VectorDBService):
    """Milvus 向量数据库服务实现"""
    
    def __init__(self, config: VectorDBConfig):
        super().__init__(config)
        self.client = None
        self.collections = {}  # 缓存已获取的集合
    
    def initialize(self) -> bool:
        """初始化Milvus客户端"""
        try:
            from pymilvus import connections, Collection, utility
            
            # 连接参数
            connect_params = {
                "host": self.config.milvus_host,
                "port": self.config.milvus_port,
            }
            
            # 如果有用户名和密码，添加到连接参数
            if self.config.milvus_user:
                connect_params["user"] = self.config.milvus_user
            if self.config.milvus_password:
                connect_params["password"] = self.config.milvus_password
            
            logger.info(f"初始化Milvus连接: {self.config.milvus_host}:{self.config.milvus_port}")
            connections.connect(
                alias="default",
                **connect_params
            )
            
            # 测试连接
            from pymilvus import utility
            utility.list_collections()  # 测试连接是否成功
            
            self.client = True  # 标记为已连接
            
            # 如果指定了数据库，切换到该数据库
            if self.config.milvus_database:
                from pymilvus import db
                db.using_database(self.config.milvus_database)
                logger.info(f"切换到数据库: {self.config.milvus_database}")
            
            self._initialized = True
            logger.info("✅ Milvus服务初始化成功")
            return True
            
        except ImportError:
            logger.error("pymilvus 未安装，请运行: pip install pymilvus")
            self._initialized = False
            return False
        except Exception as e:
            logger.error(f"初始化Milvus服务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._initialized = False
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        if not self._initialized:
            return False
        try:
            from pymilvus import utility
            return utility.has_collection(collection_name)
        except Exception as e:
            logger.error(f"检查集合是否存在失败: {e}")
            return False
    
    def create_collection(self, collection_name: str, embedding_dimension: int) -> bool:
        """创建集合"""
        if not self._initialized:
            return False
        try:
            from pymilvus import Collection, FieldSchema, CollectionSchema, DataType
            
            if self.collection_exists(collection_name):
                logger.info(f"集合 {collection_name} 已存在")
                return True
            
            # 定义集合的字段
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=255),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dimension),
                FieldSchema(name="document", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=255),
            ]
            
            # 创建集合schema
            schema = CollectionSchema(
                fields=fields,
                description="客服知识库集合"
            )
            
            # 创建集合
            collection = Collection(
                name=collection_name,
                schema=schema
            )
            
            # 创建索引
            index_params = {
                "metric_type": "L2",  # 使用L2距离
                "index_type": "IVF_FLAT",  # 简单索引类型，可根据数据量调整
                "params": {"nlist": 1024}
            }
            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            # 加载集合到内存
            collection.load()
            
            logger.info(f"✅ 创建Milvus集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_collection_count(self, collection_name: str) -> int:
        """获取集合中的文档数量"""
        if not self._initialized:
            return 0
        try:
            from pymilvus import Collection
            collection = Collection(collection_name)
            if not collection.has_index():
                # 如果集合没有索引，可能还未初始化，返回0
                return 0
            # 确保集合已加载（如果未加载，这里会加载）
            try:
                collection.load()
            except:
                pass  # 如果已经加载，忽略错误
            return collection.num_entities
        except Exception as e:
            logger.error(f"获取集合文档数量失败: {e}")
            return 0
    
    def add_documents(
        self, 
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """添加文档到集合"""
        if not self._initialized:
            return False
        try:
            from pymilvus import Collection
            
            collection = Collection(collection_name)
            collection.load()
            
            # 获取集合的字段信息，以适配不同的表结构
            schema = collection.schema
            field_names = [field.name for field in schema.fields]
            
            # 准备数据，根据实际字段名组织
            data = {}
            
            # 处理各个字段
            if "id" in field_names:
                # 如果id是Int64类型，转换为整数
                id_field = next((f for f in schema.fields if f.name == "id"), None)
                if id_field and str(id_field.dtype) == "INT64":
                    data["id"] = [int(id_str) if id_str.isdigit() else hash(id_str) for id_str in ids]
                else:
                    data["id"] = ids
            
            if "embedding" in field_names:
                data["embedding"] = embeddings
            
            # 根据不同的表结构映射字段
            if "document" in field_names:
                data["document"] = documents
            elif "content" in field_names:
                # 用户现有表结构使用 content 字段
                data["content"] = documents
            
            # 元数据字段映射
            if "source" in field_names:
                data["source"] = [meta.get('source', meta.get('file_name', '')) for meta in metadatas]
            if "file_name" in field_names:
                data["file_name"] = [meta.get('file_name', meta.get('source', '')) for meta in metadatas]
            
            if "type" in field_names:
                data["type"] = [meta.get('type', 'unknown') for meta in metadatas]
            if "chunk_method" in field_names:
                data["chunk_method"] = [meta.get('chunk_method', '') for meta in metadatas]
            if "pc_type" in field_names:
                data["pc_type"] = [meta.get('pc_type', '') for meta in metadatas]
            
            if "question" in field_names:
                data["question"] = [meta.get('question', '') for meta in metadatas]
            if "title" in field_names:
                data["title"] = [meta.get('title', '') for meta in metadatas]
            
            if "index" in field_names:
                # 如果没有提供index，使用id的索引位置
                data["index"] = [meta.get('index', i) for i, meta in enumerate(metadatas)]
            
            if "Column" in field_names:
                data["Column"] = [meta.get('Column', '') for meta in metadatas]
            
            # 按照schema字段顺序组织数据
            ordered_data = []
            for field_name in field_names:
                if field_name in data:
                    ordered_data.append(data[field_name])
                else:
                    # 如果字段缺失，填充默认值
                    field = next((f for f in schema.fields if f.name == field_name), None)
                    if field:
                        if "VARCHAR" in str(field.dtype):
                            ordered_data.append([''] * len(ids))
                        elif "INT" in str(field.dtype):
                            ordered_data.append([0] * len(ids))
            
            # 插入数据
            collection.insert(ordered_data)
            collection.flush()  # 确保数据持久化
            
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def search(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int
    ) -> Dict[str, Any]:
        """搜索相似文档"""
        if not self._initialized:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        try:
            from pymilvus import Collection
            from pymilvus.exceptions import MilvusException
            
            collection = Collection(collection_name)
            collection.load()
            
            # 获取集合schema以确定输出字段
            schema = collection.schema
            field_names = [field.name for field in schema.fields]
            
            # 构建输出字段列表（排除向量字段）
            output_fields = []
            document_field = None
            if "document" in field_names:
                document_field = "document"
                output_fields.append("document")
            elif "content" in field_names:
                document_field = "content"
                output_fields.append("content")
            
            # 添加可能的元数据字段
            metadata_fields = ["source", "file_name", "type", "chunk_method", "pc_type", 
                             "question", "title", "index", "Column"]
            for field in metadata_fields:
                if field in field_names and field not in output_fields:
                    output_fields.append(field)
            
            # 获取索引的metric_type
            metric_type = "L2"  # 默认
            indexes = collection.indexes
            if indexes and len(indexes) > 0:
                index_params = indexes[0].params
                metric_type = index_params.get("metric_type", "L2")
            
            # 构建过滤表达式：只检索 child 和 structure 类型的 chunk
            # 检索条件：
            # 1. parent_child_split 类型且 pc_type == "child" 的 chunk
            # 2. structure 类型的 chunk
            filter_expr = None
            if "chunk_method" in field_names and "pc_type" in field_names:
                # 构建过滤表达式
                filter_expr = '(chunk_method == "parent_child_split" and pc_type == "child") or (chunk_method == "structure")'
                logger.debug(f"[向量搜索] 应用过滤条件: {filter_expr}")
            
            # Milvus搜索
            search_params = {
                "metric_type": metric_type,
                "params": {"nprobe": 10}
            }
            
            results = collection.search(
                data=query_embeddings,
                anns_field="embedding",
                param=search_params,
                limit=n_results,
                expr=filter_expr,  # 添加过滤表达式
                output_fields=output_fields if output_fields else None
            )
            
            # 辅助函数：安全地获取实体字段值
            def get_entity_field(entity, field_name: str, default: Any = None) -> Any:
                """安全地获取实体字段值，支持属性访问和字典访问"""
                # 先检查字段是否在输出字段列表中（避免触发Milvus异常）
                if field_name not in output_fields:
                    return default
                try:
                    # 直接尝试属性访问（避免hasattr触发异常）
                    return getattr(entity, field_name)
                except (AttributeError, MilvusException):
                    try:
                        # 尝试字典访问
                        if hasattr(entity, '__getitem__'):
                            return entity[field_name]
                    except (KeyError, TypeError, MilvusException):
                        pass
                    return default
                except Exception:
                    # 捕获所有其他异常
                    return default
            
            # 转换结果为统一格式
            documents = []
            metadatas = []
            distances = []
            
            for hits in results:
                doc_list = []
                meta_list = []
                dist_list = []
                
                for hit in hits:
                    entity = hit.entity
                    # 获取文档内容（优先使用document，否则使用content）
                    doc_content = get_entity_field(entity, document_field) or get_entity_field(entity, "content", "")
                    doc_list.append(doc_content if doc_content else "")
                    
                    # 构建元数据（适配不同的表结构）
                    metadata = {}
                    if "source" in field_names:
                        metadata["source"] = get_entity_field(entity, "source") or get_entity_field(entity, "file_name", "未知")
                    elif "file_name" in field_names:
                        metadata["source"] = get_entity_field(entity, "file_name", "未知")
                    else:
                        metadata["source"] = "未知"
                    
                    metadata["type"] = get_entity_field(entity, "type", "unknown")
                    metadata["question"] = get_entity_field(entity, "question", "")
                    metadata["title"] = get_entity_field(entity, "title", "")
                    
                    # 保留其他字段
                    if "file_name" in field_names:
                        metadata["file_name"] = get_entity_field(entity, "file_name", "")
                    if "chunk_method" in field_names:
                        metadata["chunk_method"] = get_entity_field(entity, "chunk_method", "")
                    if "pc_type" in field_names:
                        metadata["pc_type"] = get_entity_field(entity, "pc_type", "")
                    if "index" in field_names:
                        metadata["index"] = get_entity_field(entity, "index")
                    if "Column" in field_names:
                        metadata["Column"] = get_entity_field(entity, "Column", "")
                    
                    # 保存 ID 用于后续查询
                    if hasattr(hit, 'id'):
                        metadata["id"] = hit.id
                    
                    meta_list.append(metadata)
                    
                    # 距离转换（COSINE距离需要转换为相似度）
                    distance = float(hit.distance)
                    if metric_type == "COSINE":
                        # COSINE距离：距离越小，相似度越高
                        # 如果需要，可以转换为相似度: similarity = 1 - distance
                        dist_list.append(distance)
                    else:
                        dist_list.append(distance)
                
                documents.append(doc_list)
                metadatas.append(meta_list)
                distances.append(dist_list)
            
            return {
                'documents': documents,
                'metadatas': metadatas,
                'distances': distances,
                '_collection_name': collection_name  # 返回集合名称用于 parent-child 处理
            }
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}


def create_vector_db_service(config: VectorDBConfig) -> VectorDBService:
    """
    工厂函数：根据配置创建向量数据库服务实例
    
    Args:
        config: 向量数据库配置
        
    Returns:
        向量数据库服务实例
    """
    provider = config.provider.lower()
    
    if provider == "chromadb":
        service = ChromaDBVectorDBService(config)
    elif provider == "milvus":
        service = MilvusVectorDBService(config)
    else:
        raise ValueError(f"不支持的向量数据库提供者: {provider}，支持: chromadb, milvus")
    
    # 初始化服务
    if not service.initialize():
        raise RuntimeError(f"向量数据库服务初始化失败: {provider}")
    
    return service

