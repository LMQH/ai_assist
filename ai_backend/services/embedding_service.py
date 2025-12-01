"""
嵌入向量服务抽象层
支持多种嵌入服务提供者（Ollama、OpenAI等），便于灵活切换
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """嵌入服务配置"""
    # 从config模块导入默认配置
    from config import (
        EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_HOST,
        EMBEDDING_API_KEY, DASHSCOPE_API_KEY, EMBEDDING_TIMEOUT,
        EMBEDDING_DIMENSIONS
    )
    
    provider: str = EMBEDDING_PROVIDER  # ollama, openai, dashscope, qwen
    model: str = EMBEDDING_MODEL
    host: Optional[str] = EMBEDDING_HOST  # 对于ollama或DashScope base_url
    api_key: Optional[str] = EMBEDDING_API_KEY or DASHSCOPE_API_KEY  # 对于openai/dashscope等
    timeout: int = EMBEDDING_TIMEOUT  # 超时时间（秒）
    dimensions: Optional[int] = EMBEDDING_DIMENSIONS  # 向量维度（仅对支持自定义维度的模型有效，如DashScope text-embedding-v4）


class EmbeddingService(ABC):
    """嵌入向量服务抽象基类"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化嵌入服务"""
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量列表
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入向量（可选，用于性能优化）
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表的列表
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        pass
    
    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self._initialized


class OllamaEmbeddingService(EmbeddingService):
    """Ollama 嵌入服务实现"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self.ollama_client = None
        self._embedding_dim = None
    
    def initialize(self) -> bool:
        """初始化Ollama客户端"""
        try:
            import ollama
            
            host = self.config.host or "http://localhost:11434"
            logger.info(f"初始化Ollama嵌入服务，连接: {host}")
            
            self.ollama_client = ollama.Client(host=host)
            
            # 测试连接
            logger.info("正在测试Ollama连接...")
            models = self.ollama_client.list()
            logger.info(f"✅ Ollama连接成功\n可用模型: {[m.model for m in models.models]}")
            
            # 测试获取嵌入向量维度
            test_embedding = self.embed("test")
            self._embedding_dim = len(test_embedding)
            logger.info(f"嵌入向量维度: {self._embedding_dim}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"初始化Ollama嵌入服务失败: {e}")
            self._initialized = False
            return False
    
    def embed(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        if not self._initialized:
            raise RuntimeError("Ollama嵌入服务未初始化")
        
        try:
            response = self.ollama_client.embed(
                model=self.config.model,
                input=text
            )
            
            embeddings = response.get('embeddings', [])
            if not embeddings or len(embeddings) == 0:
                raise ValueError("生成的嵌入向量为空")
            
            return embeddings[0]  # 返回第一个（通常只有一个）
            
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        # Ollama 支持批量处理，但这里逐个处理以保证兼容性
        # 如果需要优化，可以实现真正的批量处理
        results = []
        for i, text in enumerate(texts):
            try:
                embedding = self.embed(text)
                results.append(embedding)
                
                # 每10个显示一次进度
                if (i + 1) % 10 == 0:
                    logger.info(f"批量嵌入进度: {i + 1}/{len(texts)}")
            except Exception as e:
                logger.warning(f"批量嵌入第 {i + 1} 个文本失败: {e}")
                # 返回空向量或跳过
                results.append([])
        
        return results
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        if self._embedding_dim is None:
            # 如果还没测试过，先测试一次
            test_embedding = self.embed("test")
            self._embedding_dim = len(test_embedding)
        return self._embedding_dim


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI 嵌入服务实现（预留接口）"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self.openai_client = None
    
    def initialize(self) -> bool:
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            
            logger.info("初始化OpenAI嵌入服务...")
            self.openai_client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.host  # 可以用于自定义base_url
            )
            
            # 测试连接
            test_embedding = self.embed("test")
            self._initialized = True
            logger.info("✅ OpenAI嵌入服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化OpenAI嵌入服务失败: {e}")
            self._initialized = False
            return False
    
    def embed(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        if not self._initialized:
            raise RuntimeError("OpenAI嵌入服务未初始化")
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.config.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.config.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"批量生成嵌入向量失败: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        test_embedding = self.embed("test")
        return len(test_embedding)


class DashScopeEmbeddingService(EmbeddingService):
    """阿里云 DashScope (Qwen) 嵌入服务实现"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self.openai_client = None
        self._embedding_dim = None  # 将在初始化时确定
    
    def initialize(self) -> bool:
        """初始化DashScope客户端"""
        try:
            import os
            from openai import OpenAI
            
            # 从环境变量或配置中获取API Key
            api_key = self.config.api_key or os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DashScope API Key未设置，请设置 EMBEDDING_API_KEY 或 DASHSCOPE_API_KEY 环境变量")
            
            # base_url 可以从配置的 host 获取，或使用默认值
            base_url = self.config.host or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            
            logger.info(f"初始化DashScope嵌入服务...")
            logger.info(f"Base URL: {base_url}")
            logger.info(f"Model: {self.config.model}")
            if self.config.dimensions:
                logger.info(f"指定维度: {self.config.dimensions}")
            
            self.openai_client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            # 先设置初始化状态，以便测试连接
            self._initialized = True
            
            # 测试连接
            try:
                test_embedding = self.embed("test")
                self._embedding_dim = len(test_embedding)
                logger.info(f"✅ DashScope嵌入服务初始化成功，向量维度: {self._embedding_dim}")
                return True
            except Exception as test_error:
                # 测试失败，重置状态
                self._initialized = False
                raise test_error
            
        except Exception as e:
            logger.error(f"初始化DashScope嵌入服务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._initialized = False
            return False
    
    def embed(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        if not self._initialized:
            raise RuntimeError("DashScope嵌入服务未初始化")
        
        try:
            # 构建请求参数
            request_params = {
                "model": self.config.model,
                "input": text
            }
            
            # 如果配置了dimensions参数，添加到请求中
            # DashScope text-embedding-v4 支持通过 dimensions 参数指定向量维度
            if self.config.dimensions:
                request_params["dimensions"] = self.config.dimensions
                logger.debug(f"使用指定维度: {self.config.dimensions}")
            
            response = self.openai_client.embeddings.create(**request_params)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            # 构建请求参数
            request_params = {
                "model": self.config.model,
                "input": texts
            }
            
            # 如果配置了dimensions参数，添加到请求中
            if self.config.dimensions:
                request_params["dimensions"] = self.config.dimensions
            
            response = self.openai_client.embeddings.create(**request_params)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"批量生成嵌入向量失败: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        if self._embedding_dim is None:
            # 如果还没测试过，先测试一次
            test_embedding = self.embed("test")
            self._embedding_dim = len(test_embedding)
        return self._embedding_dim


def create_embedding_service(config: EmbeddingConfig) -> EmbeddingService:
    """
    工厂函数：根据配置创建嵌入服务实例
    
    Args:
        config: 嵌入服务配置
        
    Returns:
        嵌入服务实例
    """
    provider = config.provider.lower()
    
    if provider == "ollama":
        service = OllamaEmbeddingService(config)
    elif provider == "openai":
        service = OpenAIEmbeddingService(config)
    elif provider == "dashscope" or provider == "qwen":
        service = DashScopeEmbeddingService(config)
    else:
        raise ValueError(f"不支持的嵌入服务提供者: {provider}，支持: ollama, openai, dashscope, qwen")
    
    # 初始化服务
    if not service.initialize():
        raise RuntimeError(f"嵌入服务初始化失败: {provider}")
    
    return service

