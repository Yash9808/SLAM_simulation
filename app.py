import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import numpy as np
import random
import threading
import time
import os

# Global state
pose = {"x": 0, "z": 0, "angle": 0}
trajectory = [(0, 0)]
obstacle_hits = []
color_index = 0
rgb_colors = ['red', 'green', 'blue']
noise_enabled = True
obstacles = []
auto_mode = False

# Generate obstacles
def generate_obstacles(count=10):
    return [{"x": random.uniform(-8, 8), "z": random.uniform(-8, 8), "radius": random.uniform(0.5, 1.2)} for _ in range(count)]

# Check collision
def check_collision(x, z):
    for obs in obstacles:
        dist = np.sqrt((obs["x"] - x)**2 + (obs["z"] - z)**2)
        if dist <= obs["radius"] + 0.2:
            return True
    return False

# Reset simulation
def reset_sim(count):
    global pose, trajectory, obstacles, obstacle_hits, color_index
    pose = {"x": 0, "z": 0, "angle": 0}
    trajectory.clear()
    trajectory.append((0, 0))
    obstacle_hits.clear()
    color_index = 0
    obstacles.clear()
    obstacles.extend(generate_obstacles(int(count)))
    return render_env(), render_slam_map(), None, f"Simulation reset with {count} obstacles"

# Toggle noise
def toggle_noise():
    global noise_enabled
    noise_enabled = not noise_enabled
    return "Noise: ON" if noise_enabled else "Noise: OFF"

# Move robot (manual or automatic)
def move_robot(direction):
    global pose, trajectory
    step = 1; d = direction.upper()
    dx, dz = 0, 0
    if d=='W': dz=step; pose["angle"]=90
    elif d=='S': dz=-step; pose["angle"]=-90
    elif d=='A': dx=-step; pose["angle"]=180
    elif d=='D': dx=step; pose["angle"]=0
    else:
        return render_env(), render_slam_map(), None, "❌ Invalid Key"
    nx, nz = pose["x"]+dx, pose["z"]+dz
    if check_collision(nx, nz):
        return render_env(), render_slam_map(), "collision1.wav", "🚫 Collision!"
    pose["x"], pose["z"] = nx, nz
    if noise_enabled:
        trajectory.append((pose["x"]+random.uniform(-0.1,0.1),
                           pose["z"]+random.uniform(-0.1,0.1)))
    else:
        trajectory.append((pose["x"], pose["z"]))
    return render_env(), render_slam_map(), None, f"Moved {d}"

# Render environment
def render_env():
    global obstacle_hits
    fig, ax = plt.subplots()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_title("SLAM Environment")
    try:
        bg = mpimg.imread("map.png")
        ax.imshow(bg, extent=(-10, 10, -10, 10), alpha=0.2)
    except:
        pass
    for obs in obstacles:
        ax.add_patch(plt.Circle((obs["x"], obs["z"]), obs["radius"], color="gray", alpha=0.6))
    ax.plot(pose["x"], pose["z"], 'ro', markersize=8)
    angles = np.linspace(0, 2*np.pi, 24)
    for ang in angles:
        for r in np.linspace(0, 3, 30):
            scan_x = pose["x"] + r * np.cos(ang)
            scan_z = pose["z"] + r * np.sin(ang)
            if check_collision(scan_x, scan_z):
                ax.plot([pose["x"], scan_x], [pose["z"], scan_z], 'g-', linewidth=0.5)
                obstacle_hits.append((scan_x, scan_z))
                break
    plt.close(fig)
    return fig

# Render SLAM map
def render_slam_map():
    global color_index
    fig, ax = plt.subplots()
    ax.set_title("SLAM Trajectory Map")
    x_vals = [x for x, z in trajectory]
    z_vals = [z for x, z in trajectory]
    ax.plot(x_vals, z_vals, 'bo-', markersize=3)
    ax.grid(True)
    if obstacle_hits:
        current_color = rgb_colors[color_index % 3]
        for hit in obstacle_hits[-20:]:
            ax.plot(hit[0], hit[1], 'o', color=current_color, markersize=6)
        color_index += 1
    plt.close(fig)
    return fig

# Handle manual input
def handle_text_input(direction):
    return move_robot(direction.strip().upper())

# Auto move loop
def auto_move_loop(update_outputs_fn):
    global auto_mode
    directions = ['W', 'A', 'S', 'D']
    while auto_mode:
        random.shuffle(directions)
        for dir in directions:
            env, slam, audio, msg = move_robot(dir)
            update_outputs_fn(env, slam, audio, f"[AUTO] {msg}")
            time.sleep(1)
            if not auto_mode:
                break

# Toggle auto mode
def toggle_auto(update_fn):
    global auto_mode
    auto_mode = not auto_mode
    if auto_mode:
        thread = threading.Thread(target=auto_move_loop, args=(update_fn,))
        thread.start()
        return "🟢 Auto Mode ON"
    else:
        return "🔴 Auto Mode OFF"

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 SLAM Simulation — Manual & Automatic Navigation")
    obstacle_slider = gr.Slider(1, 20, value=10, step=1, label="Obstacle Count")
    direction_input = gr.Textbox(label="Type W / A / S / D", placeholder="e.g., W")
    status = gr.Textbox(label="Status")
    audio = gr.Audio(label="Collision Sound", interactive=False)

    with gr.Row():
        with gr.Column():
            env_plot = gr.Plot(label="Robot + Environment View")
        with gr.Column():
            slam_plot = gr.Plot(label="SLAM Trajectory Map")

    with gr.Row():
        w = gr.Button("⬆️ W")
        a = gr.Button("⬅️ A")
        s = gr.Button("⬇️ S")
        d = gr.Button("➡️ D")
        reset = gr.Button("🔄 Reset")
        toggle = gr.Button("🔀 Toggle Noise")
        auto_btn = gr.Button("🤖 Toggle Auto Mode")

    w.click(fn=move_robot, inputs=gr.State("W"), outputs=[env_plot, slam_plot, audio, status])
    a.click(fn=move_robot, inputs=gr.State("A"), outputs=[env_plot, slam_plot, audio, status])
    s.click(fn=move_robot, inputs=gr.State("S"), outputs=[env_plot, slam_plot, audio, status])
    d.click(fn=move_robot, inputs=gr.State("D"), outputs=[env_plot, slam_plot, audio, status])

    direction_input.submit(fn=handle_text_input, inputs=direction_input, outputs=[env_plot, slam_plot, audio, status])
    reset.click(fn=reset_sim, inputs=[obstacle_slider], outputs=[env_plot, slam_plot, audio, status])
    toggle.click(fn=lambda: (None, None, None, toggle_noise()), outputs=[env_plot, slam_plot, audio, status])

    auto_btn.click(fn=lambda: toggle_auto(lambda e, s, a, t: [env_plot.update(e), slam_plot.update(s), audio.update(a), status.update(t)]),
                   outputs=[auto_btn])

demo.launch()
