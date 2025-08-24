"""图表生成和数据可视化工具类."""

import base64
import io
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


class ChartGenerator:
    """图表生成器类."""

    def __init__(self) -> None:
        """初始化图表生成器."""
        # 设置中文字体
        plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans", "Arial"]
        plt.rcParams["axes.unicode_minus"] = False

        # 设置样式
        sns.set_style("whitegrid")
        plt.style.use("seaborn-v0_8")

    def generate_line_chart(
        self,
        data: list[dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        width: int = 12,
        height: int = 6,
    ) -> str:
        """生成折线图."""
        fig, ax = plt.subplots(figsize=(width, height))

        # 准备数据
        df = pd.DataFrame(data)
        x_values = df[x_field]
        y_values = df[y_field]

        # 绘制折线图
        ax.plot(x_values, y_values, marker="o", linewidth=2, markersize=6)

        # 设置标题和标签
        if title:
            ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)

        # 格式化
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return self._fig_to_base64(fig)

    def generate_bar_chart(
        self,
        data: list[dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        color: str = "skyblue",
        width: int = 10,
        height: int = 6,
    ) -> str:
        """生成柱状图."""
        fig, ax = plt.subplots(figsize=(width, height))

        # 准备数据
        df = pd.DataFrame(data)
        x_values = df[x_field]
        y_values = df[y_field]

        # 绘制柱状图
        bars = ax.bar(x_values, y_values, color=color, alpha=0.8)

        # 在柱子上添加数值
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha="center",
                va="bottom",
            )

        # 设置标题和标签
        if title:
            ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)

        # 格式化
        ax.grid(True, alpha=0.3, axis="y")
        plt.xticks(rotation=45)
        plt.tight_layout()

        return self._fig_to_base64(fig)

    def generate_pie_chart(
        self,
        data: list[dict[str, Any]],
        label_field: str,
        value_field: str,
        title: str = "",
        colors: list[str] | None = None,
        width: int = 8,
        height: int = 8,
    ) -> str:
        """生成饼图."""
        fig, ax = plt.subplots(figsize=(width, height))

        # 准备数据
        df = pd.DataFrame(data)
        labels = df[label_field]
        values = df[value_field]

        # 默认颜色
        if not colors:
            colors = plt.colormaps["Set3"](np.linspace(0, 1, len(labels)))

        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
            textprops={"fontsize": 10},
        )

        # 设置标题
        if title:
            ax.set_title(title, fontsize=16, fontweight="bold", pad=20)

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_heatmap(
        self,
        data: list[dict[str, Any]],
        x_field: str,
        y_field: str,
        value_field: str,
        title: str = "",
        width: int = 10,
        height: int = 8,
    ) -> str:
        """生成热力图."""
        fig, ax = plt.subplots(figsize=(width, height))

        # 准备数据
        df = pd.DataFrame(data)
        pivot_table = df.pivot(index=y_field, columns=x_field, values=value_field)

        # 绘制热力图
        sns.heatmap(
            pivot_table,
            annot=True,
            cmap="YlOrRd",
            center=pivot_table.mean().mean(),
            ax=ax,
            fmt=".1f",
        )

        # 设置标题
        if title:
            ax.set_title(title, fontsize=16, fontweight="bold", pad=20)

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_multi_line_chart(
        self,
        data: dict[str, list[dict[str, Any]]],
        x_field: str,
        y_field: str,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        width: int = 12,
        height: int = 6,
    ) -> str:
        """生成多线图表."""
        fig, ax = plt.subplots(figsize=(width, height))

        colors = plt.colormaps["tab10"](np.linspace(0, 1, len(data)))

        for i, (series_name, series_data) in enumerate(data.items()):
            df = pd.DataFrame(series_data)
            x_values = df[x_field]
            y_values = df[y_field]

            ax.plot(
                x_values,
                y_values,
                marker="o",
                linewidth=2,
                markersize=4,
                color=colors[i],
                label=series_name,
            )

        # 设置标题和标签
        if title:
            ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)

        # 添加图例
        ax.legend()

        # 格式化
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return self._fig_to_base64(fig)

    def generate_dashboard_chart(
        self,
        system_metrics: dict[str, float],
        teaching_trends: list[dict[str, Any]],
        user_statistics: dict[str, int],
    ) -> dict[str, str]:
        """生成监控大屏图表组合."""
        charts = {}

        # 1. 系统状态仪表盘
        charts["system_status"] = self._generate_gauge_chart(system_metrics, "系统状态监控")

        # 2. 教学趋势图
        if teaching_trends:
            charts["teaching_trends"] = self.generate_line_chart(
                teaching_trends,
                "date",
                "avg_score",
                title="教学效果趋势",
                xlabel="时间",
                ylabel="平均分数",
            )

        # 3. 用户分布饼图
        user_data = [{"type": k, "count": v} for k, v in user_statistics.items()]
        charts["user_distribution"] = self.generate_pie_chart(
            user_data, "type", "count", title="用户类型分布"
        )

        return charts

    def _generate_gauge_chart(
        self,
        metrics: dict[str, float],
        title: str = "",
    ) -> str:
        """生成仪表盘图表."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(title, fontsize=16, fontweight="bold")

        metric_names = list(metrics.keys())[:4]  # 最多显示4个指标

        for _i, (ax, metric_name) in enumerate(zip(axes.flat, metric_names, strict=False)):
            value = metrics[metric_name]

            # 创建半圆仪表盘
            theta = np.linspace(0, np.pi, 100)
            r = 1

            # 绘制背景弧
            ax.plot(r * np.cos(theta), r * np.sin(theta), "lightgray", linewidth=8)

            # 绘制数值弧
            value_theta = np.linspace(0, np.pi * (value / 100), int(100 * value / 100))
            color = "red" if value > 80 else "orange" if value > 60 else "green"
            ax.plot(r * np.cos(value_theta), r * np.sin(value_theta), color, linewidth=8)

            # 添加数值文本
            ax.text(
                0,
                -0.3,
                f"{value:.1f}%",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
            )
            ax.text(0, -0.5, metric_name, ha="center", va="center", fontsize=10)

            ax.set_xlim(-1.2, 1.2)
            ax.set_ylim(-0.6, 1.2)
            ax.set_aspect("equal")
            ax.axis("off")

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _fig_to_base64(self, fig: Any) -> str:
        """将matplotlib图形转换为base64编码字符串."""
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
        buffer.seek(0)

        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"


class DataFormatter:
    """数据格式化工具类."""

    @staticmethod
    def format_time_series(
        data: list[dict[str, Any]],
        time_field: str,
        value_field: str,
        interval: str = "1H",
    ) -> list[dict[str, Any]]:
        """格式化时间序列数据."""
        df = pd.DataFrame(data)
        df[time_field] = pd.to_datetime(df[time_field])

        # 按时间间隔重采样
        df_resampled = df.set_index(time_field).resample(interval)[value_field].mean()

        return [
            {"timestamp": timestamp.isoformat(), "value": value}
            for timestamp, value in df_resampled.items()
            if not pd.isna(value)
        ]

    @staticmethod
    def calculate_percentiles(
        values: list[float], percentiles: list[float] | None = None
    ) -> dict[str, float]:
        """计算百分位数."""
        if percentiles is None:
            percentiles = [50, 75, 90, 95, 99]
        np_values = np.array(values)
        return {f"p{int(p)}": float(np.percentile(np_values, p)) for p in percentiles}

    @staticmethod
    def moving_average(
        data: list[dict[str, Any]],
        value_field: str,
        window: int = 7,
    ) -> list[dict[str, Any]]:
        """计算移动平均."""
        df = pd.DataFrame(data)
        df[f"{value_field}_ma"] = df[value_field].rolling(window=window).mean()

        return list(df.to_dict("records"))

    @staticmethod
    def detect_anomalies(
        data: list[dict[str, Any]],
        value_field: str,
        threshold: float = 3.0,
    ) -> list[dict[str, Any]]:
        """检测异常值."""
        df = pd.DataFrame(data)
        values = df[value_field]

        # 使用Z-score检测异常
        z_scores = np.abs((values - values.mean()) / values.std())
        df["is_anomaly"] = z_scores > threshold
        df["z_score"] = z_scores

        return list(df.to_dict("records"))


class ChartColorPalette:
    """图表颜色调色板."""

    # 预定义颜色主题
    THEMES = {
        "default": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
        "pastel": ["#AEC7E8", "#FFBB78", "#98DF8A", "#FF9896", "#C5B0D5"],
        "dark": ["#1f1f1f", "#17becf", "#bcbd22", "#7f7f7f", "#e377c2"],
        "professional": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#592941"],
    }

    @classmethod
    def get_colors(cls, theme: str = "default", count: int = 5) -> list[str]:
        """获取指定主题的颜色列表."""
        colors = cls.THEMES.get(theme, cls.THEMES["default"])

        # 如果需要的颜色数量超过预定义，则循环使用
        if count > len(colors):
            return (colors * (count // len(colors) + 1))[:count]

        return colors[:count]

    @staticmethod
    def generate_gradient(start_color: str, end_color: str, steps: int = 10) -> list[str]:
        """生成渐变色列表."""
        import matplotlib.colors as mcolors

        # 创建颜色映射
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "gradient", [start_color, end_color], N=steps
        )

        return [mcolors.to_hex(cmap(i / (steps - 1))) for i in range(steps)]
