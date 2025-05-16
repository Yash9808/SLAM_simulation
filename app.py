import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import numpy as np
import random

pose = {"x": 0, "z": 0, "angle": 0}
trajectory = [(0, 0)]
noise_enabled = True

# Obstacles
obstacles = [
    {"x": 2, "z": 3, "radius": 0.7},
    {"x": -2, "z": -2, "radius": 1.0},
    {"x": 0, "z": 5, "radius": 0.8},
]

def toggle_noise(enabled):
    global noise_enabled
    noise_enabled = enabled
    return "Noise: ON" if noise_enabled else "Noise: OFF"

def reset_sim():
    global pose, trajectory
    pose = {"x": 0, "z": 0, "angle": 0}
    trajectory = [(0, 0)]
    return render_env(), render_slam_map(), "Simulation Reset!"

def check_collision(x, z):
    for obs in obstacles:
        dist = np.sqrt((obs["x"] - x)**2 + (obs["z"] - z)**2)
        if dist <= obs["radius"] + 0.2:
            return True
    return False

def move_robot(direction):
    global pose, trajectory
    step = 1
    if direction == "W":
        new_x, new_z = pose["x"], pose["z"] - step
        pose["angle"] = 90
    elif direction == "S":
        new_x, new_z = pose["x"], pose["z"] + step
        pose["angle"] = -90
    elif direction == "A":
        new_x, new_z = pose["x"] - step, pose["z"]
        pose["angle"] = 180
    elif direction == "D":
        new_x, new_z = pose["x"] + step, pose["z"]
        pose["angle"] = 0
    else:
        return render_env(), render_slam_map(), "Invalid Key"

    if check_collision(new_x, new_z):
        return render_env(), render_slam_map(), "🚫 Collision detected!"

    pose["x"], pose["z"] = new_x, new_z
    if noise_enabled:
        noisy_x = pose["x"] + random.uniform(-0.1, 0.1)
        noisy_z = pose["z"] + random.uniform(-0.1, 0.1)
        trajectory.append((noisy_x, noisy_z))
    else:
        trajectory.append((pose["x"], pose["z"]))
    return render_env(), render_slam_map(), "Moved " + direction

def render_env():
    fig, ax = plt.subplots()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_title("SLAM Environment View")

    # Real map background
    try:
        bg = mpimg.imread("map.png")
        ax.imshow(bg, extent=(-10, 10, -10, 10), alpha=0.2, zorder=0)
    except:
        pass

    # Obstacles
    for obs in obstacles:
        circ = plt.Circle((obs["x"], obs["z"]), obs["radius"], color="gray", alpha=0.6)
        ax.add_patch(circ)

    # Robot
    ax.plot(pose["x"], pose["z"], 'ro', markersize=8)

    # Simulate lidar scan lines
    angles = np.linspace(0, 2*np.pi, 24)
    for ang in angles:
        for r in np.linspace(0, 3, 30):
            scan_x = pose["x"] + r * np.cos(ang)
            scan_z = pose["z"] + r * np.sin(ang)
            if check_collision(scan_x, scan_z):
                ax.plot([pose["x"], scan_x], [pose["z"], scan_z], 'g-', linewidth=0.5)
                break
    return fig

def render_slam_map():
    fig, ax = plt.subplots()
    ax.set_title("SLAM Trajectory Map")
    x_vals = [x for x, z in trajectory]
    z_vals = [z for x, z in trajectory]
    ax.plot(x_vals, z_vals, 'bo-', markersize=3)
    ax.grid(True)
    return fig

with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Advanced SLAM Sim: Obstacles, Noise, LiDAR, Real-Time Path")

    status_text = gr.Textbox(label="Status")

    with gr.Row():
        with gr.Column():
            env_plot = gr.Plot(label="Robot + Sensor View")
        with gr.Column():
            slam_plot = gr.Plot(label="SLAM Map")

    with gr.Row():
        w = gr.Button("⬆️ W")
        a = gr.Button("⬅️ A")
        s = gr.Button("⬇️ S")
        d = gr.Button("➡️ D")
        reset = gr.Button("🔄 Reset")
        toggle = gr.Button("🔀 Toggle Noise")

    w.click(lambda: move_robot("W"), outputs=[env_plot, slam_plot, status_text])
    s.click(lambda: move_robot("S"), outputs=[env_plot, slam_plot, status_text])
    a.click(lambda: move_robot("A"), outputs=[env_plot, slam_plot, status_text])
    d.click(lambda: move_robot("D"), outputs=[env_plot, slam_plot, status_text])
    reset.click(reset_sim, outputs=[env_plot, slam_plot, status_text])
    toggle.click(lambda: (None, None, toggle_noise(not noise_enabled)), outputs=[env_plot, slam_plot, status_text])

demo.launch()
