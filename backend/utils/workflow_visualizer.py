# AI智能面试辅助系统V1.0，作者刘梦畅
"""从已编译的 LangGraph/LangChain Graph 自动生成系统架构图。"""

import re
import shutil
import subprocess
import sys
from collections import defaultdict
from io import BytesIO
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import matplotlib.pyplot as plt
    from PIL import Image as PILImage
except ImportError:
    print("错误：缺少可视化库，请安装：pip install pillow matplotlib")
    raise SystemExit(1)


def _dot_escape(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "")
        .replace("\n", "\\n")
    )


def _display_name(name: str) -> str:
    if name == "__start__":
        return "START"
    if name == "__end__":
        return "END"
    return name


def _graph_to_dot(
    graph,
    *,
    root_agent_name: str | None = None,
    collapse_middleware: bool = True,
) -> str:
    """Convert the official Graph to a readable architecture projection."""

    connected_ids = {
        node_id
        for edge in graph.edges
        for node_id in (edge.source, edge.target)
    }
    connected_nodes = {
        node_id: node
        for node_id, node in graph.nodes.items()
        if node_id in connected_ids
    }
    middleware_ids = {
        node_id
        for node_id, node in connected_nodes.items()
        if "Middleware" in node.name
    }
    visible_nodes = {
        node_id: node
        for node_id, node in connected_nodes.items()
        if not collapse_middleware or node_id not in middleware_ids
    }
    node_refs = {node_id: f"n{index}" for index, node_id in enumerate(visible_nodes)}

    if collapse_middleware:
        adjacency = defaultdict(list)
        for edge in graph.edges:
            if edge.source in connected_nodes and edge.target in connected_nodes:
                adjacency[edge.source].append(edge)

        projected_edges = []
        for source_id in visible_nodes:
            for first_edge in adjacency[source_id]:
                if first_edge.target in visible_nodes:
                    projected_edges.append(
                        (source_id, first_edge.target, first_edge.data, first_edge.conditional)
                    )
                    continue
                if first_edge.target not in middleware_ids:
                    continue

                stack = [(first_edge.target, first_edge.data)]
                visited = set()
                while stack:
                    current_id, path_label = stack.pop()
                    if current_id in visited:
                        continue
                    visited.add(current_id)
                    for next_edge in adjacency[current_id]:
                        label = path_label if path_label is not None else next_edge.data
                        if next_edge.target in visible_nodes:
                            if source_id == next_edge.target:
                                continue
                            if (
                                visible_nodes[source_id].name == "__start__"
                                and visible_nodes[next_edge.target].name == "__end__"
                            ):
                                continue
                            projected_edges.append(
                                (source_id, next_edge.target, label, label is not None)
                            )
                        elif next_edge.target in middleware_ids:
                            stack.append((next_edge.target, label))
        render_edges = list(dict.fromkeys(projected_edges))
    else:
        render_edges = [
            (edge.source, edge.target, edge.data, edge.conditional)
            for edge in graph.edges
            if edge.source in visible_nodes and edge.target in visible_nodes
        ]

    groups: dict[str, list[str]] = defaultdict(list)
    root_nodes: list[str] = []
    for node_id in visible_nodes:
        if ":" in node_id:
            group_name, _ = node_id.split(":", 1)
            groups[group_name].append(node_id)
        else:
            root_nodes.append(node_id)

    middleware_groups: dict[str, list[str]] = defaultdict(list)
    if collapse_middleware:
        for node_id in middleware_ids:
            group_name = node_id.split(":", 1)[0] if ":" in node_id else "__root__"
            middleware_groups[group_name].append(node_id)

    lines = [
        "digraph architecture {",
        '  graph [rankdir=TB, bgcolor="white", pad="0.25", nodesep="0.35", ranksep="0.55", compound=true];',
        '  node [shape=box, style="rounded,filled", fillcolor="#f5f3ff", color="#8b5cf6", fontname="Microsoft YaHei", fontsize=10];',
        '  edge [color="#4b5563", fontname="Microsoft YaHei", fontsize=9, arrowsize=0.7];',
    ]

    def add_node(node_id: str, indent: str = "  ") -> None:
        node = visible_nodes[node_id]
        label = _dot_escape(_display_name(node.name))
        shape = "oval" if node.name in {"__start__", "__end__"} else "box"
        lines.append(f'{indent}{node_refs[node_id]} [label="{label}", shape={shape}];')

    def add_middleware_summary(group_name: str, indent: str) -> str | None:
        middleware_node_ids = middleware_groups.get(group_name, [])
        if not middleware_node_ids:
            return None
        class_names = sorted({
            connected_nodes[node_id].name.split(".", 1)[0].split("[", 1)[0]
            for node_id in middleware_node_ids
        })
        safe_group_name = re.sub(r"[^A-Za-z0-9_]", "_", group_name)
        summary_ref = f"middleware_{safe_group_name}"
        label = _dot_escape("Middleware hooks (collapsed)\n" + "\n".join(class_names))
        lines.append(
            f'{indent}{summary_ref} [label="{label}", shape=note, '
            'fillcolor="#fff7ed", color="#f59e0b"];'
        )
        return summary_ref

    if root_agent_name:
        lines.append("  subgraph cluster_root_agent {")
        lines.append(f'    label="{_dot_escape(root_agent_name)} / create_agent";')
        lines.append('    color="#7c3aed"; penwidth=1.5; style="rounded";')
        for node_id in root_nodes:
            add_node(node_id, "    ")
        root_middleware_ref = add_middleware_summary("__root__", "    ")
        lines.append("  }")
    else:
        for node_id in root_nodes:
            add_node(node_id)
        root_middleware_ref = add_middleware_summary("__root__", "  ")

    for index, (group_name, node_ids) in enumerate(groups.items()):
        node_names = {visible_nodes[node_id].name for node_id in node_ids}
        is_create_agent = {"model", "tools"}.issubset(node_names) or any(
            "Middleware" in name for name in node_names
        )
        suffix = " / create_agent" if is_create_agent else " / subgraph"
        lines.append(f"  subgraph cluster_{index} {{")
        lines.append(f'    label="{_dot_escape(group_name + suffix)}";')
        lines.append('    color="#7c3aed"; penwidth=1.5; style="rounded";')
        for node_id in node_ids:
            add_node(node_id, "    ")
        group_middleware_ref = add_middleware_summary(group_name, "    ")
        lines.append("  }")
        if group_middleware_ref:
            for node_id in node_ids:
                if visible_nodes[node_id].name in {"model", "tools"}:
                    lines.append(
                        f'  {group_middleware_ref} -> {node_refs[node_id]} '
                        '[style="dotted", arrowhead="none", color="#f59e0b"];'
                    )

    if root_middleware_ref:
        for node_id in root_nodes:
            if visible_nodes[node_id].name in {"model", "tools"}:
                lines.append(
                    f'  {root_middleware_ref} -> {node_refs[node_id]} '
                    '[style="dotted", arrowhead="none", color="#f59e0b"];'
                )

    for source_id, target_id, edge_data, is_conditional in render_edges:
        attributes = []
        if edge_data is not None:
            attributes.append(f'label="{_dot_escape(edge_data)}"')
        if is_conditional:
            attributes.append('style="dashed"')
        attribute_text = f" [{', '.join(attributes)}]" if attributes else ""
        lines.append(
            f"  {node_refs[source_id]} -> {node_refs[target_id]}{attribute_text};"
        )

    lines.append("}")
    return "\n".join(lines)


def _render_with_graphviz(graph, *, root_agent_name: str | None = None) -> PILImage.Image:
    dot_command = shutil.which("dot")
    if not dot_command:
        raise RuntimeError("未找到 Graphviz dot，请先安装 Graphviz 并加入 PATH")

    completed = subprocess.run(
        [dot_command, "-Tpng", "-Gdpi=120"],
        input=_graph_to_dot(graph, root_agent_name=root_agent_name).encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Graphviz 渲染失败: {detail}")
    return PILImage.open(BytesIO(completed.stdout)).convert("RGB")


def generate_combined_graph(show_window: bool = False) -> Path:
    """Load the real compiled graphs, expand Agent subgraphs, and render them."""

    from backend.graph.agents.consultant_agent import consultant_agent
    from backend.graph.workflow import create_interview_graph

    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    print("正在从已编译 Graph 自动生成系统架构图...")
    graph_specs = [
        {
            "name": "面试工作流",
            "graph": create_interview_graph().get_graph(xray=True),
            "root_agent_name": None,
            "title": "AI智能面试工作流程\n(create_agent 子图 / Middleware 折叠)",
        },
        {
            "name": "顾问 Agent",
            "graph": consultant_agent.get_graph(xray=True),
            "root_agent_name": "consultant_agent",
            "title": "面试顾问智能体\n(create_agent 子图)",
        },
    ]

    images = []
    for spec in graph_specs:
        print(f"  - 渲染 {spec['name']}...")
        images.append(
            _render_with_graphviz(
                spec["graph"],
                root_agent_name=spec["root_agent_name"],
            )
        )

    padding = 50
    title_height = 90
    max_height = max(image.height for image in images)
    total_width = sum(image.width for image in images) + padding * (len(images) - 1)
    total_height = max_height + title_height
    combined = PILImage.new("RGB", (total_width, total_height), "white")

    current_x = 0
    for image in images:
        combined.paste(image, (current_x, title_height))
        current_x += image.width + padding

    fig, ax = plt.subplots(figsize=(total_width / 100, total_height / 100), dpi=100)
    ax.axis("off")
    ax.imshow(combined)

    current_x = 0
    for image, spec in zip(images, graph_specs):
        ax.text(
            current_x + image.width / 2,
            45,
            spec["title"],
            fontsize=16,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(facecolor="#f0f0f0", edgecolor="none", pad=10, alpha=0.8),
        )
        current_x += image.width + padding

    output_path = project_root / "system_architecture_graph.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight", facecolor="white")
    print(f"系统架构图已保存到: {output_path}")

    if show_window:
        plt.show()
    else:
        plt.close(fig)
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true", help="生成后显示图片")
    args = parser.parse_args()
    generate_combined_graph(args.show)
