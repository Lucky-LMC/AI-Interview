# AI智能面试辅助系统V1.0，作者刘梦畅
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from io import BytesIO
from backend.graph.workflow import create_interview_graph

try:
    from PIL import Image as PILImage  # pillow
    import matplotlib.pyplot as plt
    HAS_VIZ_LIBS = True
except ImportError:
    HAS_VIZ_LIBS = False   
if __name__ == "__main__":
    # 可视化
    # 设置中文字体，避免中文显示警告
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']  # 设置中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    graph = create_interview_graph()
    img_bytes = graph.get_graph(xray=True).draw_mermaid_png()  # 生成工作流图的 PNG 二进制数据
    img = PILImage.open(BytesIO(img_bytes))  # 将二进制数据转换为图像对象
    plt.figure(figsize=(6, 5))  # 创建画布，设置大小
    plt.imshow(img)  # 显示图像
    plt.axis('off')  # 隐藏坐标轴
    plt.title("AI智能面试工作流程图", fontsize=16, fontweight='bold', pad=20)  # 添加中文标题
    plt.tight_layout()  # 自动调整布局
    plt.show()  # 显示窗口
