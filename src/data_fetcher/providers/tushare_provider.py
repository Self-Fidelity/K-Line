"""Tushare 数据源 Provider 实现"""

import time
from datetime import datetime
from typing import Optional
import pandas as pd

from src.utils.logger import get_logger
from src.config import settings

logger = get_logger(__name__)


class TushareProvider:
    """Tushare Pro 数据获取 Provider
    
    批量查询优化策略：
    - daily 接口每次最多返回 6000 条数据
    - 单只股票全量历史约 6000 条（23 年），全量时每只股票需单独 1 次请求
    - 增量更新时（如最近 1 年约 250 条），一次可批量拉取约 24 只股票
    - adj_factor 接口同样支持批量，与 daily 共享批量分组
    """
    
    name = "tushare"
    
    # Tushare daily 接口单页最大返回行数
    MAX_ROWS_PER_REQUEST = 6000
    # 为安全留 10% 余量
    SAFE_MAX_ROWS = 5400
    # 每年约 250 个交易日（用于估算）
    TRADING_DAYS_PER_YEAR = 250
    
    def __init__(self, token: Optional[str] = None):
        """初始化 Tushare Provider
        
        Args:
            token: Tushare Pro API token，如果为 None 则尝试从配置获取
        """
        self._token = token
        self._pro = None
        self.retry_count = 3
        self.retry_delay = 1.0
        self.request_interval = 0.12  # 约 8 次/秒，500 次/分钟限制下很宽松
    
    def _get_pro(self):
        """获取 Tushare Pro 接口实例（延迟加载）"""
        if self._pro is None:
            import tushare as ts
            token = self._token
            if not token:
                # 尝试从数据库配置获取
                try:
                    from src.data_storage import get_storage_instance
                    storage = get_storage_instance()
                    token = storage.get_update_config("tushare_token", "")
                except Exception as e:
                    logger.warning(f"[Tushare] 从数据库获取 token 失败: {e}")
            
            if not token:
                raise ValueError("Tushare token 未设置，请在数据更新管理中配置")
            
            self._pro = ts.pro_api(token)
            logger.info("[Tushare] Pro API 已初始化")
        
        return self._pro
    
    @staticmethod
    def _normalize_code(stock_code: str) -> str:
        """将股票代码转换为 Tushare 格式（带后缀）
        
        Args:
            stock_code: 如 '000001'
        
        Returns:
            如 '000001.SZ'
        """
        if "." in stock_code:
            return stock_code
        
        code = str(stock_code).strip()
        if code.startswith("6"):
            return f"{code}.SH"
        elif code.startswith("8") or code.startswith("4"):
            # 北交所/新三板
            return f"{code}.BJ"
        else:
            # 0 开头（深圳主板）、3 开头（创业板）
            return f"{code}.SZ"
    
    @staticmethod
    def _denormalize_code(ts_code: str) -> str:
        """将 Tushare 格式的股票代码转换为纯数字代码
        
        Args:
            ts_code: 如 '000001.SZ'
        
        Returns:
            如 '000001'
        """
        return ts_code.split(".")[0]
    
    def _estimate_batch_size(self, start_date: str = "", end_date: str = "") -> int:
        """根据日期范围估算每次请求可批量拉取的股票数量
        
        Tushare daily 接口每次最多返回 6000 条数据。
        单只股票全量历史约 6000 条，因此全量时 batch_size=1。
        增量更新时，根据日期范围估算每只股票的交易日数量，
        计算一次请求可以容纳多少只股票。
        
        Args:
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
        
        Returns:
            建议的批量大小（至少为 1）
        """
        if not start_date and not end_date:
            return 1
        
        try:
            if start_date:
                s = datetime.strptime(start_date, "%Y%m%d")
            else:
                s = datetime(1990, 1, 1)
            if end_date:
                e = datetime.strptime(end_date, "%Y%m%d")
            else:
                e = datetime.now()
            
            natural_days = max(1, (e - s).days)
            trading_days = max(1, int(natural_days * self.TRADING_DAYS_PER_YEAR / 365))
            batch_size = max(1, self.SAFE_MAX_ROWS // trading_days)
            return min(batch_size, 200)
        except Exception:
            return 1
    
    def _fetch_adj_factor(
        self,
        ts_codes: list[str],
        start_date: str = "",
        end_date: str = "",
    ) -> pd.DataFrame:
        """批量获取复权因子"""
        if not ts_codes:
            return pd.DataFrame()
        
        pro = self._get_pro()
        ts_code_str = ",".join(ts_codes)
        params = {"ts_code": ts_code_str}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        for attempt in range(self.retry_count):
            try:
                adj_df = pro.adj_factor(**params)
                time.sleep(self.request_interval)
                return adj_df
            except Exception as e:
                if attempt < self.retry_count - 1:
                    logger.warning(f"[Tushare] 批量获取复权因子失败（尝试 {attempt + 1}/{self.retry_count}）: {e}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"[Tushare] 批量获取复权因子失败: {e}")
                    raise
        
        return pd.DataFrame()
    
    def _apply_adj_to_df(
        self,
        df: pd.DataFrame,
        adj_df: pd.DataFrame,
        adjust: str,
    ) -> pd.DataFrame:
        """对单只股票的 DataFrame 应用复权因子"""
        if df.empty or adj_df.empty:
            return df
        
        try:
            df = df.merge(adj_df[["trade_date", "adj_factor"]], on="trade_date", how="left")
            df = df.sort_values("trade_date", ascending=True).reset_index(drop=True)
            df["adj_factor"] = df["adj_factor"].ffill().fillna(1.0)
            
            if adjust == "hfq":
                df["open"] = df["open"] * df["adj_factor"]
                df["high"] = df["high"] * df["adj_factor"]
                df["low"] = df["low"] * df["adj_factor"]
                df["close"] = df["close"] * df["adj_factor"]
                if "pre_close" in df.columns:
                    df["pre_close"] = df["pre_close"] * df["adj_factor"]
            elif adjust == "qfq":
                latest_factor = df["adj_factor"].max()
                df["open"] = df["open"] * df["adj_factor"] / latest_factor
                df["high"] = df["high"] * df["adj_factor"] / latest_factor
                df["low"] = df["low"] * df["adj_factor"] / latest_factor
                df["close"] = df["close"] * df["adj_factor"] / latest_factor
                if "pre_close" in df.columns:
                    df["pre_close"] = df["pre_close"] * df["adj_factor"] / latest_factor
            
            df = df.drop(columns=["adj_factor"])
            df = df.sort_values("trade_date", ascending=False).reset_index(drop=True)
        except Exception as e:
            logger.warning(f"[Tushare] 应用复权因子失败: {e}")
        
        return df
    
    def get_daily_data(
        self,
        stock_code: str,
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> pd.DataFrame:
        """获取单只股票的日K线数据"""
        logger.debug(f"[Tushare] 获取股票 {stock_code} 的日K线数据，日期范围: {start_date} ~ {end_date}")
        
        ts_code = self._normalize_code(stock_code)
        pro = self._get_pro()
        
        for attempt in range(self.retry_count):
            try:
                params = {
                    "ts_code": ts_code,
                }
                
                if start_date:
                    params["start_date"] = start_date
                if end_date:
                    params["end_date"] = end_date
                
                # 获取不复权日线数据
                df = pro.daily(**params)
                
                if df.empty:
                    logger.warning(f"[Tushare] 股票 {stock_code} 未获取到数据")
                    return pd.DataFrame()
                
                # 如果需要复权，获取复权因子
                if adjust in ("hfq", "qfq"):
                    df = self._apply_adjustment(df, ts_code, adjust)
                
                # 标准化列名
                df = self._standardize_columns(df)
                
                # 按日期升序排列
                df = df.sort_values("date").reset_index(drop=True)
                
                logger.debug(f"[Tushare] 成功获取股票 {stock_code} {len(df)} 条数据")
                
                # 限速
                time.sleep(self.request_interval)
                
                return df
                
            except Exception as e:
                if attempt < self.retry_count - 1:
                    logger.warning(
                        f"[Tushare] 获取股票 {stock_code} 数据失败（尝试 {attempt + 1}/{self.retry_count}）: {e}"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"[Tushare] 获取股票 {stock_code} 数据失败: {e}", exc_info=True)
                    raise
        
        return pd.DataFrame()
    
    def _apply_adjustment(self, df: pd.DataFrame, ts_code: str, adjust: str) -> pd.DataFrame:
        """应用复权因子（单只股票，兼容旧接口）
        
        Args:
            df: 原始日线数据
            ts_code: Tushare 格式代码
            adjust: 'hfq' 或 'qfq'
        
        Returns:
            复权后的数据
        """
        try:
            adj_df = self._fetch_adj_factor([ts_code])
            
            if adj_df.empty:
                logger.warning(f"[Tushare] 股票 {ts_code} 未获取到复权因子")
                return df
            
            return self._apply_adj_to_df(df, adj_df, adjust)
            
        except Exception as e:
            logger.warning(f"[Tushare] 应用复权因子失败: {e}")
        
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化 DataFrame 列名"""
        column_mapping = {
            "trade_date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "vol": "volume",
            "amount": "amount",
            "pct_chg": "pct_chg",
            "change": "change",
        }
        
        # Tushare 列名已经是英文，但需要转换日期列
        df = df.rename(columns=column_mapping)
        
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        
        # Tushare 的 vol 单位是手，转换为股（乘以 100）
        if "volume" in df.columns:
            df["volume"] = df["volume"] * 100
        
        # Tushare 的 amount 单位是千元，转换为元（乘以 1000）
        if "amount" in df.columns:
            df["amount"] = df["amount"] * 1000
        
        # 选择需要的列
        required_columns = ["date", "open", "close", "high", "low", "volume", "amount"]
        available_columns = [col for col in required_columns if col in df.columns]
        
        optional_columns = ["pct_chg", "change"]
        for col in optional_columns:
            if col in df.columns:
                available_columns.append(col)
        
        df = df[available_columns].copy()
        return df
    
    def get_stock_list(self, market: str = "all") -> pd.DataFrame:
        """获取股票列表"""
        try:
            pro = self._get_pro()
            
            # 获取所有A股列表
            df_all = pro.stock_basic(
                exchange="",
                list_status="L",
                fields="ts_code,symbol,name,area,industry,list_date,exchange"
            )
            time.sleep(self.request_interval)
            
            if df_all.empty:
                logger.warning("[Tushare] 获取股票列表返回空数据")
                return pd.DataFrame(columns=["code", "name", "market"])
            
            # 使用 symbol 作为纯数字代码
            df_all["code"] = df_all["symbol"]
            
            # 根据交易所判断市场类型
            def _detect_market(row) -> str:
                code = str(row["code"])
                exchange = str(row.get("exchange", ""))
                if code.startswith("688") or code.startswith("689"):
                    return "kcb"
                elif code.startswith("3"):
                    return "cyb"
                elif exchange == "BSE" or code.startswith("8") or code.startswith("4"):
                    # 北交所
                    return "main"  # 归类到主板或新建 bse，这里先归类到 main
                else:
                    return "main"
            
            df_all["market"] = df_all.apply(_detect_market, axis=1)
            
            if market != "all":
                df_all = df_all[df_all["market"] == market].copy()
            
            df = df_all[["code", "name", "market"]].copy()
            logger.debug(f"[Tushare] 获取到 {len(df)} 只股票，市场: {market}")
            return df
            
        except Exception as e:
            logger.error(f"[Tushare] 获取股票列表失败: {e}", exc_info=True)
            raise
    
    def get_daily_data_batch(
        self,
        stock_codes: list[str],
        start_date: str = "",
        end_date: str = "",
        adjust: str = "hfq",
    ) -> dict[str, pd.DataFrame]:
        """批量获取多只股票的日K线数据（Tushare 优化版）
        
        利用 Tushare daily 接口支持多股票同时查询的能力，
        根据日期范围智能计算每批可拉取的股票数量，
        将请求次数降至最低。
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            adjust: 复权类型
        
        Returns:
            字典，key 为股票代码，value 为对应的 DataFrame
        """
        if not stock_codes:
            return {}
        
        batch_size = self._estimate_batch_size(start_date, end_date)
        
        # 如果估算批量为 1，直接 fallback 到父类默认实现（逐只串行）
        # 这样全量更新时每只股票仍走最优单只路径
        if batch_size <= 1:
            return super().get_daily_data_batch(stock_codes, start_date, end_date, adjust)
        
        logger.info(
            f"[Tushare] 批量获取 {len(stock_codes)} 只股票，"
            f"日期范围: {start_date or '全部'} ~ {end_date or '最新'}, "
            f"预估 batch_size: {batch_size}"
        )
        
        pro = self._get_pro()
        results: dict[str, pd.DataFrame] = {}
        failed_codes: list[str] = []
        total_batches = (len(stock_codes) + batch_size - 1) // batch_size
        
        for batch_idx, i in enumerate(range(0, len(stock_codes), batch_size), 1):
            batch = stock_codes[i:i + batch_size]
            ts_codes = [self._normalize_code(c) for c in batch]
            ts_code_str = ",".join(ts_codes)
            
            try:
                # 批量获取 daily 数据
                params = {"ts_code": ts_code_str}
                if start_date:
                    params["start_date"] = start_date
                if end_date:
                    params["end_date"] = end_date
                
                df = pro.daily(**params)
                time.sleep(self.request_interval)
                
                if df.empty:
                    logger.warning(f"[Tushare] 批次 {batch_idx}/{total_batches} 返回空数据")
                    failed_codes.extend(batch)
                    continue
                
                # 批量获取复权因子（与 daily 同日期范围）
                adj_df = pd.DataFrame()
                if adjust in ("hfq", "qfq"):
                    adj_df = self._fetch_adj_factor(ts_codes, start_date, end_date)
                
                # 按股票分组处理
                for code in batch:
                    ts_code = self._normalize_code(code)
                    stock_df = df[df["ts_code"] == ts_code].copy()
                    
                    if stock_df.empty:
                        failed_codes.append(code)
                        continue
                    
                    # 应用复权
                    if adjust in ("hfq", "qfq") and not adj_df.empty:
                        stock_adj_df = adj_df[adj_df["ts_code"] == ts_code].copy()
                        stock_df = self._apply_adj_to_df(stock_df, stock_adj_df, adjust)
                    
                    # 标准化
                    stock_df = self._standardize_columns(stock_df)
                    stock_df = stock_df.sort_values("date").reset_index(drop=True)
                    results[code] = stock_df
                
                if batch_idx % 10 == 0 or batch_idx == total_batches:
                    logger.info(
                        f"[Tushare] 批量进度 {batch_idx}/{total_batches} | "
                        f"成功 {len(results)} 只，失败 {len(failed_codes)} 只"
                    )
                    
            except Exception as e:
                logger.error(f"[Tushare] 批次 {batch_idx}/{total_batches} 失败: {e}")
                failed_codes.extend(batch)
                continue
        
        if failed_codes:
            logger.warning(f"[Tushare] 批量获取完成，失败 {len(failed_codes)} 只: {failed_codes[:10]}")
        
        logger.info(
            f"[Tushare] 批量获取完成，成功 {len(results)}/{len(stock_codes)} 只，"
            f"共发起 {total_batches} 次 API 请求"
        )
        return results
    
    def test_connection(self) -> dict:
        """测试 Tushare 连接"""
        try:
            pro = self._get_pro()
            # 尝试获取股票列表的前几条来测试
            df = pro.stock_basic(exchange="", list_status="L", fields="ts_code,name")
            if not df.empty:
                return {"success": True, "message": "Tushare 连接正常"}
            return {"success": False, "message": "Tushare 返回空数据"}
        except Exception as e:
            return {"success": False, "message": f"Tushare 连接失败: {str(e)}"}
