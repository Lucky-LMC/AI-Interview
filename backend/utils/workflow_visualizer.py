# AI智能面试辅助系统V1.0，作者刘梦畅
"""
工作流可视化脚本
生成包含了主面试工作流和客服 Agent 的系统全览图
"""
import sys
from pathlib import Path

# Add project root to Python path
# 修正路径：backend/utils/workflow_visualizer.py -> backend/utils/ -> backend/ -> project_root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from io import BytesIO
try:
    from PIL import Image as PILImage  # pillow
    import matplotlib.pyplot as plt
    HAS_VIZ_LIBS = True
except ImportError:
    HAS_VIZ_LIBS = False
    print("错误：缺少可视化库，请安装：pip install pillow matplotlib")
    sys.exit(1)


def generate_combined_graph(show_window=False):
    """
    生成包含面试工作流和客服 Agent 的系统总览图
    确保两个图表并排展示且节点大小一致
    """
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    print("正在生成系统工作流全览图...")
    
    graphs = [
        {
            "name": "面试工作流",
            "import": lambda: __import__('backend.graph.workflow', fromlist=['create_interview_graph']).create_interview_graph(),
            "title": "AI智能面试工作流程"
        },
        {
            "name": "客服 Agent",
            "import": lambda: __import__('backend.graph.agents.customer_service_agent', fromlist=['customer_service_agent']).customer_service_agent,
            "title": "面试客服 Agent 流程"
        }
    ]
    
    images = []
    
    # 1. 生成原始图片
    for g_conf in graphs:
        try:
            print(f"  - 渲染 {g_conf['name']}...")
            # 执行 lambda 函数以获取图对象
            graph_obj = g_conf["import"]()
            img_bytes = graph_obj.get_graph(xray=True).draw_mermaid_png()
            img = PILImage.open(BytesIO(img_bytes))
            images.append(img)
        except Exception as e:
            print(f"❌ 生成 {g_conf['name']} 失败: {e}")
            # 出错时继续，避免全盘失败
            continue

    if not images:
        print("❌ 未能生成任何图表")
        return

    # 2. 保持原图尺寸，不进行缩放，以确保节点文字大小一致
    # 直接使用原始图片，高度不一致时在画布上用白色填充
    resized_images = images
    max_height = max(img.height for img in images)
    
    # 3. 创建合并画布
    padding = 50  # 图片间距
    titles_height = 80 # 标题区域高度
    total_width = sum(img.width for img in resized_images) + padding * (len(images) - 1)
    total_height = max_height + titles_height
    
    # 创建白色背景的大图
    combined_img = PILImage.new('RGB', (total_width, total_height), 'white')
    
    # 4. 粘贴图片并绘制
    current_x = 0
    
    # 使用 Matplotlib 进行更方便的文字渲染
    fig, ax = plt.subplots(figsize=(total_width/100, total_height/100), dpi=100)
    
    # 隐藏坐标轴
    ax.axis('off')
    
    # 在 matplotlib 中绘制组合图
    for idx, (img, conf) in enumerate(zip(resized_images, graphs)):
        # 粘贴到 PIL 图片
        # 计算垂直居中位置 (如果需要) 或者顶部对齐
        # 这里使用顶部对齐，更符合流程图展示习惯
        combined_img.paste(img, (current_x, titles_height))
        
        current_x += img.width + padding

    # 显示合并后的图片
    ax.imshow(combined_img)
    
    # 添加子标题
    current_x = 0
    for idx, (img, conf) in enumerate(zip(resized_images, graphs)):
        center_x = current_x + img.width / 2
        ax.text(center_x, 40, conf['title'], 
                fontsize=16, fontweight='bold', 
                ha='center', va='center',
                bbox=dict(facecolor='#f0f0f0', edgecolor='none', pad=10, alpha=0.8))
        current_x += img.width + padding

    plt.tight_layout()
    
    # 保存
    output_path = project_root / "system_architecture_graph.png"
    plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
    print(f"✅ 系统全览图已保存到: {output_path}")
    
    if show_window:
        print("\n提示：关闭图片窗口以退出程序")
        plt.show()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true", help="生成后显示图片")
    args = parser.parse_args()
    
    generate_combined_graph(args.show)
