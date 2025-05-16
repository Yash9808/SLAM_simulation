import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

pose = {"x": 0, "z": 0, "angle": 0}
trajectory = [(0, 0)]

def move_robot(direction):
    step = 1
    if direction == "W":
        pose["z"] -= step
        pose["angle"] = 90
    elif direction == "S":
        pose["z"] += step
        pose["angle"] = -90
    elif direction == "A":
        pose["x"] -= step
        pose["angle"] = 180
    elif direction == "D":
        pose["x"] += step
        pose["angle"] = 0
    trajectory.append((pose["x"], pose["z"]))
    return render_robot_view(), render_slam_map()

def render_robot_view():
    fig, ax = plt.subplots()
    ax.set_title("Robot View (Top Down)")
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)

    # Draw the robot as a triangle
    robot_size = 0.5
    angle_rad = np.deg2rad(pose["angle"])
    x, z = pose["x"], pose["z"]
    triangle = np.array([
        [0, robot_size],
        [-robot_size/2, -robot_size/2],
        [robot_size/2, -robot_size/2]
    ])
    rotation_matrix = np.array([
        [np.cos(angle_rad), -np.sin(angle_rad)],
        [np.sin(angle_rad), np.cos(angle_rad)]
    ])
    rotated_triangle = triangle @ rotation_matrix.T + np.array([x, z])
    robot_patch = patches.Polygon(rotated_triangle, closed=True, color='red')
    ax.add_patch(robot_patch)

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
    gr.Markdown("## 🤖 Robot Simulation (Triangle) + 🗺️ SLAM Path")

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
