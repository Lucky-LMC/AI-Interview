# AI智能面试辅助系统V1.0，作者刘梦畅
"""
工作流可视化脚本
生成包含了主面试工作流和客服 Agent 的系统全览图
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

    def get_interview_graph():
        """创建与实际八节点路由一致的高层面试工作流图。"""
        from langchain_core.runnables.graph import Graph

        graph = Graph()
        start = graph.add_node(None, "workflow_start")
        parse_resume = graph.add_node(None, "parse_resume")
        validate_resume = graph.add_node(None, "validate_resume")
        interviewer = graph.add_node(None, "interviewer_agent")
        review = graph.add_node(None, "review_question")
        answer = graph.add_node(None, "human_answer_interrupt")
        check_finish = graph.add_node(None, "check_finish")
        feedback = graph.add_node(None, "feedback_agent")
        report = graph.add_node(None, "generate_report")
        end = graph.add_node(None, "workflow_end")

        graph.add_edge(start, parse_resume)
        graph.add_edge(parse_resume, validate_resume)
        graph.add_edge(validate_resume, interviewer, "valid", conditional=True)
        graph.add_edge(validate_resume, end, "invalid", conditional=True)
        graph.add_edge(interviewer, review)
        graph.add_edge(review, interviewer, "rewrite once", conditional=True)
        graph.add_edge(review, answer, "approved", conditional=True)
        graph.add_edge(answer, check_finish)
        graph.add_edge(check_finish, interviewer, "continue", conditional=True)
        graph.add_edge(check_finish, feedback, "finish", conditional=True)
        graph.add_edge(feedback, report)
        graph.add_edge(report, end)
        return graph
    
    def get_consultant_graph():
        """创建与实际 Agent 策略一致的高层顾问架构图。"""
        from langchain_core.runnables.graph import Graph

        graph = Graph()
        user = graph.add_node(None, "user_question")
        agent = graph.add_node(None, "consultant_agent")
        knowledge = graph.add_node(None, "search_knowledge_base")
        web = graph.add_node(None, "tavily_search")
        response = graph.add_node(None, "streaming_response")
        graph.add_edge(user, agent)
        graph.add_edge(agent, knowledge, "required")
        graph.add_edge(knowledge, agent, "evidence")
        graph.add_edge(agent, web, "low confidence", conditional=True)
        graph.add_edge(web, agent, "sources")
        graph.add_edge(agent, response)
        return graph

    graphs = [
        {
            "name": "面试工作流",
            "import": get_interview_graph,
            "title": "AI智能面试工作流程\n(异步重试 / 超时 / 恢复)"
        },
        {
            "name": "顾问 Agent",
            "import": get_consultant_graph,
            "title": "面试顾问智能体\n(consultant_agent)"
        }
    ]
    
    images = []
    
    # 1. 生成原始图片
    for g_conf in graphs:
        try:
            print(f"  - 渲染 {g_conf['name']}...")
            # 执行 lambda 函数以获取图对象
            graph_obj = g_conf["import"]()
            graph_view = graph_obj.get_graph(xray=False) if hasattr(graph_obj, "get_graph") else graph_obj
            img_bytes = graph_view.draw_mermaid_png(max_retries=5, retry_delay=2.0)
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
