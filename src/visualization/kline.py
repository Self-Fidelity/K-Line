"""K线图可视化模块（使用Bokeh）"""

from pathlib import Path
from typing import Optional
import pandas as pd
from bokeh.plotting import figure, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, RangeTool, LabelSet, Label, Div, Range1d
from bokeh.layouts import column, row
from bokeh.io import export_png

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KLineChart:
    """K线图绘制类（使用Bokeh，输出HTML）"""
    
    def __init__(self, width: int = 1400, height: int = 700):
        """
        初始化K线图
        
        Args:
            width: 图表宽度（像素）
            height: 图表高度（像素）
        """
        self.width = width
        self.height = height
    
    def plot(
        self,
        data: pd.DataFrame,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        save_path: Optional[Path] = None,
        strategy_result: Optional[pd.DataFrame] = None,
        statistics: Optional[dict] = None,
    ) -> str:
        """
        绘制K线图（输出HTML文件）
        
        Args:
            data: 股票数据 DataFrame，必须包含 date, open, close, high, low, volume 列
            stock_code: 股票代码（可选）
            stock_name: 股票名称（可选）
            save_path: 保存路径（可选），如果为空则自动生成
            strategy_result: 策略分析结果 DataFrame（可选），包含 date, signal 列，用于标记买卖信号
        
        Returns:
            保存的HTML文件路径
        """
        # 验证数据
        required_columns = ["date", "open", "close", "high", "low", "volume"]
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"数据必须包含以下列: {required_columns}")
        
        # 准备数据
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        # 生成输出路径
        if not save_path:
            date_suffix = ""
            start_date = df["date"].min().strftime("%Y%m%d")
            end_date = df["date"].max().strftime("%Y%m%d")
            date_suffix = f"_{start_date}_{end_date}"
            
            settings.CHART_DIR.mkdir(parents=True, exist_ok=True)
            save_path = settings.CHART_DIR / f"{stock_code or 'stock'}_kline{date_suffix}.html"
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置输出文件
        output_file(str(save_path))
        
        # 准备数据源（使用索引作为x轴，消除非交易日空缺）
        df = df.reset_index(drop=True)
        df["index"] = df.index
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
        df["color"] = df.apply(lambda row: "red" if row["close"] >= row["open"] else "green", axis=1)
        df["mid"] = (df["open"] + df["close"]) / 2
        df["height"] = abs(df["close"] - df["open"])
        
        source = ColumnDataSource(df)
        
        # 创建主图（K线图）- 使用索引作为x轴
        title = f"{stock_name or ''} ({stock_code or ''}) K线图" if stock_code or stock_name else "K线图"
        p1 = figure(
            width=self.width,
            height=int(self.height * 0.7),
            title=title,
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above",
        )
        
        # 绘制K线（使用索引作为x轴）
        # 绘制上下影线
        p1.segment(
            x0="index",
            y0="low",
            x1="index",
            y1="high",
            source=source,
            color="color",
            line_width=1,
        )
        
        # 绘制实体
        p1.rect(
            x="index",
            y="mid",
            width=0.6,
            height="height",
            source=source,
            fill_color="color",
            line_color="color",
            alpha=0.8,
        )
        
        # 添加悬停工具
        hover = HoverTool(
            tooltips=[
                ("日期", "@date_str"),
                ("开盘", "@open{0.2f}"),
                ("收盘", "@close{0.2f}"),
                ("最高", "@high{0.2f}"),
                ("最低", "@low{0.2f}"),
                ("成交量", "@volume{0,0}"),
            ]
        )
        p1.add_tools(hover)
        
        # 设置x轴标签（显示日期）
        # 选择部分日期作为标签，避免过于密集
        num_labels = min(20, len(df))  # 最多显示20个标签
        step = max(1, len(df) // num_labels)
        tick_positions = list(range(0, len(df), step))
        tick_labels = [df.iloc[i]["date_str"] for i in tick_positions]
        
        p1.xaxis.ticker = tick_positions
        p1.xaxis.major_label_overrides = {pos: label for pos, label in zip(tick_positions, tick_labels)}
        p1.xaxis.major_label_orientation = 45  # 标签旋转45度
        
        # 设置标签
        p1.xaxis.axis_label = "日期"
        p1.yaxis.axis_label = "价格"
        p1.grid.grid_line_alpha = 0.3
        
        # 如果有策略结果，添加买卖信号标记
        if strategy_result is not None and not strategy_result.empty:
            # 确保策略结果的date列是datetime类型
            strategy_result = strategy_result.copy()
            strategy_result["date"] = pd.to_datetime(strategy_result["date"])
            
            # 合并策略结果和数据
            signal_df = pd.merge(
                df[["index", "date", "high"]],
                strategy_result[["date", "signal", "signal_type"]],
                on="date",
                how="inner",
            )
            
            if not signal_df.empty:
                # 买入信号（标注B，红底白字）
                buy_signals = signal_df[signal_df["signal"] == 1].copy()
                if not buy_signals.empty:
                    # 标签位置：在最高价上方2%
                    buy_signals["label_y"] = buy_signals["high"] * 1.02
                    buy_signals["label_text"] = "B"
                    buy_source = ColumnDataSource(buy_signals)
                    # 绘制标签（红底白字）
                    labels_buy = LabelSet(
                        x="index",
                        y="label_y",
                        text="label_text",
                        source=buy_source,
                        text_font_size="12pt",
                        text_color="white",
                        text_font_style="bold",
                        y_offset=8,
                        x_offset=-5,
                        background_fill_color="red",
                        background_fill_alpha=0.5,
                    )
                    p1.add_layout(labels_buy)
                
                # 卖出信号（标注S，蓝底白字）
                sell_signals = signal_df[signal_df["signal"] == -1].copy()
                if not sell_signals.empty:
                    # 标签位置：在最高价上方2%
                    sell_signals["label_y"] = sell_signals["high"] * 1.02
                    sell_signals["label_text"] = "S"
                    sell_source = ColumnDataSource(sell_signals)
                    # 绘制标签（蓝底白字）
                    labels_sell = LabelSet(
                        x="index",
                        y="label_y",
                        text="label_text",
                        source=sell_source,
                        text_font_size="12pt",
                        text_color="white",
                        text_font_style="bold",
                        y_offset=8,
                        x_offset=-5,
                        background_fill_color="blue",
                        background_fill_alpha=0.5,
                    )
                    p1.add_layout(labels_sell)
        
        # 创建成交量图（使用索引作为x轴）
        p2 = figure(
            width=self.width,
            height=int(self.height * 0.3),
            x_range=p1.x_range,
            tools="pan,wheel_zoom,box_zoom,reset",
            toolbar_location=None,
        )
        
        # 绘制成交量
        p2.vbar(
            x="index",
            top="volume",
            width=0.6,
            source=source,
            fill_color="color",
            line_color="color",
            alpha=0.6,
        )
        
        # 设置x轴标签（与主图保持一致）
        p2.xaxis.ticker = tick_positions
        p2.xaxis.major_label_overrides = {pos: label for pos, label in zip(tick_positions, tick_labels)}
        p2.xaxis.major_label_orientation = 45
        
        p2.xaxis.axis_label = "日期"
        p2.yaxis.axis_label = "成交量"
        p2.grid.grid_line_alpha = 0.3
        
        # 组合图表
        if statistics:
            # 如果有统计结果，在右侧添加统计面板
            stats_html = self._format_statistics_html(statistics)
            chart_height = int(self.height * 0.95)
            stats_div = Div(text=stats_html, width=300, height=chart_height, sizing_mode="fixed")
            chart_col = column(p1, p2, sizing_mode="fixed")
            chart = row([chart_col, stats_div], sizing_mode="fixed", width=self.width + 300)
        else:
            chart = column(p1, p2)
        
        # 保存
        save(chart)
        logger.info(f"K线图已保存到: {save_path}")
        
        return str(save_path)
    
    def _format_statistics_html(self, stats: dict) -> str:
        """
        格式化统计结果为HTML
        
        Args:
            stats: 统计结果字典
        
        Returns:
            HTML字符串
        """
        html = """
        <div style="padding: 10px; font-family: Arial, sans-serif;">
            <h3 style="margin-top: 0; color: #333;">策略统计</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
        """
        
        # 信号统计
        html += f"""
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 5px; border: 1px solid #ddd;"><strong>总信号数</strong></td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right;">{stats.get('total_signals', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">买入信号</td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right;">{stats.get('buy_signals', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">卖出信号</td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right;">{stats.get('sell_signals', 0)}</td>
                </tr>
        """
        
        # 交易统计
        html += f"""
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 5px; border: 1px solid #ddd;" colspan="2"><strong>交易统计</strong></td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">总交易次数</td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right;">{stats.get('total_trades', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">盈利交易</td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right;">{stats.get('profitable_trades', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">胜率（成功率）</td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right; color: {'green' if stats.get('win_rate', 0) >= 50 else 'red'};"><strong>{stats.get('win_rate', 0):.2f}%</strong></td>
                </tr>
        """
        
        # 收益率
        total_return = stats.get('cumulative_return', 0)
        html += f"""
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 5px; border: 1px solid #ddd;" colspan="2"><strong>收益率</strong></td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">累计收益率</td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right; color: red;"><strong>{total_return:.2f}%</strong></td>
                </tr>
        """
        
        # 风险指标
        html += f"""
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 5px; border: 1px solid #ddd;" colspan="2"><strong>风险指标</strong></td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #ddd;">最大回撤</td>
                    <td style="padding: 5px; border: 1px solid #ddd; text-align: right; color: green;"><strong>{stats.get('max_drawdown', 0):.2f}%</strong></td>
                </tr>
        """
        
        html += """
            </table>
        </div>
        """
        
        return html
    
    def plot_with_ma(
        self,
        data: pd.DataFrame,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        ma_periods: list[int] = [5, 10, 20, 30],
        save_path: Optional[Path] = None,
        strategy_result: Optional[pd.DataFrame] = None,
        statistics: Optional[dict] = None,
    ) -> str:
        """
        绘制带均线的K线图
        
        Args:
            data: 股票数据 DataFrame
            stock_code: 股票代码
            stock_name: 股票名称
            ma_periods: 均线周期列表
            save_path: 保存路径
        
        Returns:
            保存的HTML文件路径
        """
        # 计算均线
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        for period in ma_periods:
            df[f"MA{period}"] = df["close"].rolling(window=period).mean()
        
        # 生成输出路径
        if not save_path:
            date_suffix = ""
            start_date = df["date"].min().strftime("%Y%m%d")
            end_date = df["date"].max().strftime("%Y%m%d")
            date_suffix = f"_{start_date}_{end_date}"
            
            settings.CHART_DIR.mkdir(parents=True, exist_ok=True)
            save_path = settings.CHART_DIR / f"{stock_code or 'stock'}_kline_ma{date_suffix}.html"
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置输出文件
        output_file(str(save_path))
        
        # 准备数据源（使用索引作为x轴，消除非交易日空缺）
        df = df.reset_index(drop=True)
        df["index"] = df.index
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
        df["color"] = df.apply(lambda row: "red" if row["close"] >= row["open"] else "green", axis=1)
        df["mid"] = (df["open"] + df["close"]) / 2
        df["height"] = abs(df["close"] - df["open"])
        
        source = ColumnDataSource(df)
        
        # 创建主图（使用索引作为x轴）
        title = f"{stock_name or ''} ({stock_code or ''}) K线图（带均线）" if stock_code or stock_name else "K线图（带均线）"
        p1 = figure(
            width=self.width,
            height=int(self.height * 0.7),
            title=title,
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above",
        )
        
        # 绘制均线（使用索引作为x轴）
        colors = ["blue", "orange", "purple", "brown", "pink", "gray"]
        for i, period in enumerate(ma_periods):
            ma_col = f"MA{period}"
            if ma_col in df.columns:
                color = colors[i % len(colors)]
                p1.line(
                    x="index",
                    y=ma_col,
                    source=source,
                    legend_label=f"MA{period}",
                    line_width=2,
                    color=color,
                    alpha=0.8,
                )
        
        # 绘制K线（使用索引作为x轴）
        p1.segment(
            x0="index",
            y0="low",
            x1="index",
            y1="high",
            source=source,
            color="color",
            line_width=1,
        )
        
        p1.rect(
            x="index",
            y="mid",
            width=0.6,
            height="height",
            source=source,
            fill_color="color",
            line_color="color",
            alpha=0.8,
        )
        
        # 添加悬停工具
        hover = HoverTool(
            tooltips=[
                ("日期", "@date_str"),
                ("开盘", "@open{0.2f}"),
                ("收盘", "@close{0.2f}"),
                ("最高", "@high{0.2f}"),
                ("最低", "@low{0.2f}"),
                ("成交量", "@volume{0,0}"),
            ] + [(f"MA{period}", f"@MA{period}{{0.2f}}") for period in ma_periods if f"MA{period}" in df.columns]
        )
        p1.add_tools(hover)
        
        # 如果有策略结果，添加买卖信号标记
        if strategy_result is not None and not strategy_result.empty:
            # 确保策略结果的date列是datetime类型
            strategy_result = strategy_result.copy()
            strategy_result["date"] = pd.to_datetime(strategy_result["date"])
            
            # 合并策略结果和数据
            signal_df = pd.merge(
                df[["index", "date", "close"]],
                strategy_result[["date", "signal", "signal_type"]],
                on="date",
                how="inner",
            )
            
            if not signal_df.empty:
                # 买入信号（标注B，红底白字）
                buy_signals = signal_df[signal_df["signal"] == 1].copy()
                if not buy_signals.empty:
                    # 合并数据获取high价格
                    buy_signals = pd.merge(
                        buy_signals[["index", "date", "signal"]],
                        df[["index", "high"]],
                        on="index",
                        how="left",
                    )
                    # 标签位置：在最高价上方2%
                    buy_signals["label_y"] = buy_signals["high"] * 1.02
                    buy_signals["label_text"] = "B"
                    buy_source = ColumnDataSource(buy_signals)
                    # 绘制标签（红底白字）
                    labels_buy = LabelSet(
                        x="index",
                        y="label_y",
                        text="label_text",
                        source=buy_source,
                        text_font_size="12pt",
                        text_color="white",
                        text_font_style="bold",
                        y_offset=8,
                        x_offset=0,
                        background_fill_color="red",
                        background_fill_alpha=0.3,
                    )
                    p1.add_layout(labels_buy)
                
                # 卖出信号（标注S，蓝底白字）
                sell_signals = signal_df[signal_df["signal"] == -1].copy()
                if not sell_signals.empty:
                    # 合并数据获取high价格
                    sell_signals = pd.merge(
                        sell_signals[["index", "date", "signal"]],
                        df[["index", "high"]],
                        on="index",
                        how="left",
                    )
                    # 标签位置：在最高价上方2%
                    sell_signals["label_y"] = sell_signals["high"] * 1.02
                    sell_signals["label_text"] = "S"
                    sell_source = ColumnDataSource(sell_signals)
                    # 绘制标签（蓝底白字）
                    labels_sell = LabelSet(
                        x="index",
                        y="label_y",
                        text="label_text",
                        source=sell_source,
                        text_font_size="12pt",
                        text_color="white",
                        text_font_style="bold",
                        y_offset=8,
                        x_offset=0,
                        background_fill_color="blue",
                        background_fill_alpha=0.3,
                    )
                    p1.add_layout(labels_sell)
        
        # 设置x轴标签（显示日期）
        num_labels = min(20, len(df))  # 最多显示20个标签
        step = max(1, len(df) // num_labels)
        tick_positions = list(range(0, len(df), step))
        tick_labels = [df.iloc[i]["date_str"] for i in tick_positions]
        
        p1.xaxis.ticker = tick_positions
        p1.xaxis.major_label_overrides = {pos: label for pos, label in zip(tick_positions, tick_labels)}
        p1.xaxis.major_label_orientation = 45  # 标签旋转45度
        
        p1.legend.location = "top_left"
        p1.xaxis.axis_label = "日期"
        p1.yaxis.axis_label = "价格"
        p1.grid.grid_line_alpha = 0.3
        
        # 创建成交量图（使用索引作为x轴）
        p2 = figure(
            width=self.width,
            height=int(self.height * 0.3),
            x_range=p1.x_range,
            tools="pan,wheel_zoom,box_zoom,reset",
            toolbar_location=None,
        )
        
        p2.vbar(
            x="index",
            top="volume",
            width=0.6,
            source=source,
            fill_color="color",
            line_color="color",
            alpha=0.6,
        )
        
        # 设置x轴标签（与主图保持一致）
        p2.xaxis.ticker = tick_positions
        p2.xaxis.major_label_overrides = {pos: label for pos, label in zip(tick_positions, tick_labels)}
        p2.xaxis.major_label_orientation = 45
        
        p2.xaxis.axis_label = "日期"
        p2.yaxis.axis_label = "成交量"
        p2.grid.grid_line_alpha = 0.3
        
        # 组合图表
        if statistics:
            # 如果有统计结果，在右侧添加统计面板
            stats_html = self._format_statistics_html(statistics)
            chart_height = int(self.height * 0.95)
            stats_div = Div(text=stats_html, width=300, height=chart_height, sizing_mode="fixed")
            chart_col = column(p1, p2, sizing_mode="fixed")
            chart = row([chart_col, stats_div], sizing_mode="fixed", width=self.width + 300)
        else:
            chart = column(p1, p2)
        
        # 保存
        save(chart)
        logger.info(f"K线图（带均线）已保存到: {save_path}")
        
        return str(save_path)
