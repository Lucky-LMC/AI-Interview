# AI智能面试辅助系统V1.0，作者刘梦畅
"""
工作流可视化脚本
生成 LangGraph 工作流程图并保存到 docs/images/ 目录
"""
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
    print("错误：缺少可视化库，请安装：pip install pillow matplotlib")
    sys.exit(1)


if __name__ == "__main__":
    print("正在生成工作流可视化图...")
    
    # 设置中文字体，避免中文显示警告
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建工作流图
    graph = create_interview_graph()
    
    # 生成工作流图的 PNG 二进制数据（xray=True 显示子图）
    img_bytes = graph.get_graph(xray=True).draw_mermaid_png()
    img = PILImage.open(BytesIO(img_bytes))
    
    # 创建画布并添加标题
    plt.figure(figsize=(12, 10))
    plt.imshow(img)
    plt.axis('off')
    plt.title("AI智能面试工作流程图", fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    
    # 保存图片到项目根目录
    output_path = project_root / "workflow_graph.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 工作流图已保存到项目根目录: {output_path}")
    
    # 显示图片（可选）
    print("\n提示：关闭图片窗口以退出程序")
    plt.show()
