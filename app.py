import gradio as gr
import matplotlib.pyplot as plt

pose = {"x": 0, "z": 0}
trajectory = [(0, 0)]

def move_robot(direction):
    step = 1
    if direction == "W":
        pose["z"] -= step
    elif direction == "S":
        pose["z"] += step
    elif direction == "A":
        pose["x"] -= step
    elif direction == "D":
        pose["x"] += step
    trajectory.append((pose["x"], pose["z"]))
    return render_robot_view(), render_slam_map()

def render_robot_view():
    fig, ax = plt.subplots()
    ax.set_title("Robot View (Top Down)")
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.plot(pose["x"], pose["z"], "ro", label="Robot")
    ax.legend()
    ax.grid(True)
    return fig

def render_slam_map():
    fig, ax = plt.subplots()
    x_vals = [x for x, z in trajectory]
    z_vals = [z for x, z in trajectory]
    ax.plot(x_vals, z_vals, marker='o', color='blue')
    ax.set_title("SLAM Map")
    ax.set_xlabel("X")
    ax.set_ylabel("Z")
    ax.grid(True)
    return fig

with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Robot Movement + 🗺️ SLAM Path")

    with gr.Row():
        with gr.Column():
            robot_plot = gr.Plot(label="Robot View")
        with gr.Column():
            slam_plot = gr.Plot(label="SLAM Path")

    with gr.Row():
        w = gr.Button("⬆️ W")
        s = gr.Button("⬇️ S")
        a = gr.Button("⬅️ A")
        d = gr.Button("➡️ D")

    w.click(lambda: move_robot("W"), outputs=[robot_plot, slam_plot])
    s.click(lambda: move_robot("S"), outputs=[robot_plot, slam_plot])
    a.click(lambda: move_robot("A"), outputs=[robot_plot, slam_plot])
    d.click(lambda: move_robot("D"), outputs=[robot_plot, slam_plot])

demo.launch()
