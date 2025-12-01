"""
Excel数据处理工具函数
"""
import re
import os
import time
import pandas as pd
import logging
import traceback
from typing import List, Optional, Dict, Any
from pathlib import Path

from models.request_models import Message
from config import EXCEL_FILE_PATH, EXCEL_COLUMN_MAPPING

logger = logging.getLogger(__name__)

# 全局Excel数据缓存
excel_data = None
excel_data_loaded = False


def reload_excel_data():
    """强制重新加载Excel数据（清除缓存后重新加载）
    
    注意：
    - 此函数会清除缓存并重新从当前配置的路径加载Excel数据
    - 如果修改了配置文件，建议重启服务以确保配置生效
    - 也可以通过API端点 /api/excel/reload 手动刷新缓存
    """
    global excel_data, excel_data_loaded
    
    logger.info("[Excel加载] 强制重新加载Excel数据（清除缓存）")
    excel_data = None
    excel_data_loaded = False
    
    return load_excel_data()


def load_excel_data():
    """加载Excel数据到内存缓存
    支持两种配置方式：
    1. 文件路径：直接加载指定的Excel文件
    2. 文件夹路径：加载文件夹下所有.xlsx文件并合并
    """
    global excel_data, excel_data_loaded

    if excel_data_loaded:
        logger.debug("[Excel加载] 数据已加载，使用缓存")
        return excel_data

    load_start = time.time()
    try:
        # 规范化并获取绝对路径
        # 先规范化路径（处理相对路径、..等），然后转换为绝对路径
        normalized_path = os.path.normpath(EXCEL_FILE_PATH)
        excel_path = os.path.abspath(normalized_path)
        # 去除尾随分隔符（确保路径判断的准确性）
        excel_path = excel_path.rstrip(os.sep + '/')
        
        # 判断是文件还是文件夹
        if os.path.isfile(excel_path):
            # 单文件加载
            logger.info(f"[Excel加载] 检测到文件路径，开始加载Excel文件: {excel_path}")
            df = _load_single_excel_file(excel_path)
        elif os.path.isdir(excel_path):
            # 文件夹加载
            logger.info(f"[Excel加载] 检测到文件夹路径，开始加载文件夹下所有Excel文件: {excel_path}")
            df = _load_excel_files_from_directory(excel_path)
        else:
            error_msg = f"[Excel加载] ❌ 路径不存在: {excel_path}"
            logger.error(error_msg)
            excel_data = pd.DataFrame()
            excel_data_loaded = True
            return excel_data

        if df is None or df.empty:
            logger.warning("[Excel加载] ⚠️ 未加载到任何数据")
            excel_data = pd.DataFrame()
            excel_data_loaded = True
            return excel_data

        # 检查必要的列是否存在（使用英文标准列名）
        required_columns = ['session_id', 'merged_message_content', 'foreignId']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            logger.warning(f"[Excel加载] ⚠️ Excel文件缺少必要的列: {missing_columns}")
            excel_data = df
        else:
            # 检查是否存在重复的session_id
            duplicate_mask = df['session_id'].duplicated(keep='last')
            duplicate_count = duplicate_mask.sum()
            if duplicate_count > 0:
                logger.warning(f"[Excel加载] ⚠️ 发现 {duplicate_count} 条重复的session_id，将保留最后一条")
                df = df[~duplicate_mask]
            
            # 设置session_id为索引以便快速查找
            df.set_index('session_id', inplace=True)
            excel_data = df
            load_time = time.time() - load_start
            logger.info(f"[Excel加载] ✅ Excel数据加载成功，共 {len(df)} 条记录，耗时: {load_time:.3f}秒")

        excel_data_loaded = True
        return excel_data

    except Exception as e:
        load_time = time.time() - load_start
        logger.error(f"[Excel加载] ❌ 加载Excel数据失败: {e} | 耗时: {load_time:.3f}秒")
        logger.error(f"[Excel加载] 异常堆栈: {traceback.format_exc()}")
        excel_data = pd.DataFrame()
        excel_data_loaded = True
        return excel_data


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """将Excel列名映射为标准英文列名
    
    Args:
        df: 原始DataFrame
        
    Returns:
        列名已标准化的DataFrame
    """
    if df.empty:
        return df
    
    # 创建反向映射：中文列名 -> 英文标准列名
    rename_map = {}
    for english_name, mapping_info in EXCEL_COLUMN_MAPPING.items():
        chinese_names = mapping_info.get('chinese_names', [])
        for chinese_name in chinese_names:
            if chinese_name in df.columns:
                rename_map[chinese_name] = english_name
                logger.debug(f"[Excel加载] 列名映射: {chinese_name} -> {english_name}")
    
    # 应用映射
    if rename_map:
        df = df.rename(columns=rename_map)
        logger.info(f"[Excel加载] 已映射 {len(rename_map)} 个列名")
    
    return df


def _load_single_excel_file(file_path: str) -> pd.DataFrame:
    """加载单个Excel文件"""
    try:
        df = pd.read_excel(file_path)
        logger.info(f"[Excel加载] 文件 {os.path.basename(file_path)} 读取成功，行数: {len(df)}")
        # 标准化列名
        df = _normalize_column_names(df)
        return df
    except Exception as e:
        logger.error(f"[Excel加载] ❌ 加载文件 {file_path} 失败: {e}")
        return pd.DataFrame()


def _load_excel_files_from_directory(directory_path: str) -> pd.DataFrame:
    """从文件夹加载所有Excel文件并合并"""
    excel_files = []
    directory = Path(directory_path)
    
    # 查找所有.xlsx和.xls文件
    for ext in ['*.xlsx', '*.xls']:
        excel_files.extend(directory.glob(ext))
    
    # 过滤掉临时文件和非Excel文件
    valid_excel_files = []
    for excel_file in excel_files:
        file_name = excel_file.name
        # 跳过Excel临时文件（以~$开头的文件）
        if file_name.startswith('~$'):
            logger.debug(f"[Excel加载] 跳过临时文件: {file_name}")
            continue
        # 确保是真正的Excel文件扩展名
        if not (file_name.lower().endswith('.xlsx') or file_name.lower().endswith('.xls')):
            logger.debug(f"[Excel加载] 跳过非Excel文件: {file_name}")
            continue
        valid_excel_files.append(excel_file)
    
    if not valid_excel_files:
        logger.warning(f"[Excel加载] ⚠️ 文件夹 {directory_path} 中未找到任何有效的Excel文件")
        return pd.DataFrame()
    
    logger.info(f"[Excel加载] 在文件夹中找到 {len(valid_excel_files)} 个有效的Excel文件")
    
    dataframes = []
    loaded_count = 0
    failed_count = 0
    
    for excel_file in sorted(valid_excel_files):  # 按文件名排序
        try:
            df = pd.read_excel(excel_file)
            if not df.empty:
                # 标准化列名
                df = _normalize_column_names(df)
                dataframes.append(df)
                loaded_count += 1
                logger.info(f"[Excel加载] ✓ 加载文件: {excel_file.name} (行数: {len(df)})")
            else:
                logger.warning(f"[Excel加载] ⚠️ 文件 {excel_file.name} 为空，跳过")
        except Exception as e:
            failed_count += 1
            logger.error(f"[Excel加载] ❌ 加载文件 {excel_file.name} 失败: {e}")
    
    if not dataframes:
        logger.error("[Excel加载] ❌ 没有成功加载任何Excel文件")
        return pd.DataFrame()
    
    # 合并所有DataFrame
    try:
        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"[Excel加载] 成功加载 {loaded_count} 个文件，合并后总行数: {len(combined_df)}")
        if failed_count > 0:
            logger.warning(f"[Excel加载] ⚠️ {failed_count} 个文件加载失败")
        return combined_df
    except Exception as e:
        logger.error(f"[Excel加载] ❌ 合并Excel文件失败: {e}")
        return pd.DataFrame()


def extract_session_ids_from_conversation(conversation: List[Message]) -> List[str]:
    """从对话历史中提取所有可能为会话ID的数字，按时间戳排序"""
    session_id_pattern = r'\d{8,12}'  # 8-12位数字

    session_ids_with_time = []
    seen_ids = set()

    for message in conversation:
        content = message.content
        numbers = re.findall(session_id_pattern, content)
        for num in numbers:
            if len(num) >= 8 and num not in seen_ids:
                seen_ids.add(num)
                timestamp = message.timestamp if message.timestamp is not None else 0
                session_ids_with_time.append({
                    'session_id': num,
                    'timestamp': timestamp,
                })

    # 按时间戳排序（最新的在前）
    session_ids_with_time.sort(key=lambda x: x['timestamp'], reverse=True)
    return [item['session_id'] for item in session_ids_with_time]


def find_session_data_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """根据会话ID查找Excel中的相关数据"""
    global excel_data

    if excel_data is None:
        load_excel_data()

    if excel_data.empty:
        return None

    try:
        session_id_num = int(session_id) if session_id.isdigit() else None
        matched_row = None

        # 方式1: 直接数字匹配
        if session_id_num is not None and session_id_num in excel_data.index:
            matched_row = excel_data.loc[session_id_num]
        # 方式2: 字符串匹配
        elif session_id in excel_data.index:
            matched_row = excel_data.loc[session_id]
        # 方式3: 在foreignId（用户唯一标识）中查找
        else:
            if 'foreignId' in excel_data.columns:
                matched_rows = excel_data[excel_data['foreignId'].astype(str).str.contains(session_id, na=False)]
                if not matched_rows.empty:
                    matched_row = matched_rows.iloc[0]

        if matched_row is not None:
            # 提取有用的数据（使用英文标准列名）
            result = {
                'session_id': str(matched_row.name) if hasattr(matched_row, 'name') else session_id,
                'user_unique_id': str(matched_row.get('foreignId', '')),
                'conversation_content': str(matched_row.get('merged_message_content', '')),
                'phone': str(matched_row.get('phone', '')),
                'access_time': str(matched_row.get('createTime', '')),
                'start_time': str(matched_row.get('startTime', '')),
                'end_time': str(matched_row.get('endTime', '')),
                'customer_tags': str(matched_row.get('userTags', '')),
                'first_category': str(matched_row.get('category', '')),
                'session_end_reason': str(matched_row.get('closeReason', '')),
                'dialogue_rounds': str(matched_row.get('roundNumber', '')),
                'evaluation_status': str(matched_row.get('evaluation', '')),
            }

            # 尝试解析会话内容中的有用信息
            content = result['conversation_content']
            if content and content != 'nan':
                # 提取最近几条消息作为上下文
                content_lines = content.split('\n')
                recent_messages = content_lines[-10:] if len(content_lines) > 10 else content_lines
                result['recent_messages'] = recent_messages

            return result

        return None

    except Exception as e:
        logger.error(f"查找会话数据时出错: {e}")
        return None

