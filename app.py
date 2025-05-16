import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
import numpy as np
import random
import os

# Static map with obstacles
obstacles = [
    {"x": 3, "z": 3, "radius": 0.5},
    {"x": -2, "z": -2, "radius": 1.0},
    {"x": 0, "z": 5, "radius": 0.75},
]

pose = {"x": 0, "z": 0, "angle": 0}
trajectory = [(0, 0)]

def move_robot(direction):
    step = 1
    noise = 0.1  # small movement noise
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

    # Add slight noise
    noisy_x = pose["x"] + random.uniform(-noise, noise)
    noisy_z = pose["z"] + random.uniform(-noise, noise)
    trajectory.append((noisy_x, noisy_z))

    return render_robot_view(), render_slam_map()

def render_robot_view():
    fig, ax = plt.subplots()
    ax.set_title("Robot + Obstacles")
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)

    # Draw obstacles
    for obs in obstacles:
        circle = plt.Circle((obs["x"], obs["z"]), obs["radius"], color='gray', alpha=0.5)
        ax.add_patch(circle)

    # Draw robot icon (use a placeholder dot if image fails)
    try:
        img = mpimg.imread("robot.png")
        ax.imshow(img, extent=(pose["x"]-0.5, pose["x"]+0.5, pose["z"]-0.5, pose["z"]+0.5), zorder=10)
    except:
        ax.plot(pose["x"], pose["z"], "ro", label="Robot")

    ax.grid(True)
    return fig

def render_slam_map():
    fig, ax = plt.subplots()
    x_vals = [x for x, z in trajectory]
    z_vals = [z for x, z in trajectory]
    ax.plot(x_vals, z_vals, marker='o', color='blue')
    ax.set_title("SLAM Map (Noisy Path)")
    ax.set_xlabel("X")
    ax.set_ylabel("Z")
    ax.grid(True)
    return fig

with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Robot with Obstacles + Simulated SLAM + Icon")

    with gr.Row():
        with gr.Column():
            robot_plot = gr.Plot(label="Environment View")
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
