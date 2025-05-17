import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import numpy as np
import random
import threading
import time

# Global state
pose = {"x": 0, "z": 0, "angle": 0}
trajectory = [(0, 0)]
obstacle_hits = []
color_index = 0
rgb_colors = ['red', 'green', 'blue']
noise_enabled = True

mode = "Manual"
auto_running = False
obstacles = []

def generate_obstacles(count=10):
    return [{"x": random.uniform(-8, 8), "z": random.uniform(-8, 8), "radius": random.uniform(0.5, 1.2)} for _ in range(count)]

obstacles = generate_obstacles(10)

def toggle_noise():
    global noise_enabled
    noise_enabled = not noise_enabled
    return "Noise: ON" if noise_enabled else "Noise: OFF"

def reset_sim(count):
    global pose, trajectory, obstacles, obstacle_hits, color_index, auto_running
    auto_running = False
    pose = {"x": 0, "z": 0, "angle": 0}
    trajectory = [(0, 0)]
    obstacle_hits = []
    color_index = 0
    obstacles = generate_obstacles(int(count))
    return render_env(), render_slam_map(), None, f"Simulation Reset with {count} obstacles"

def check_collision(x, z):
    for obs in obstacles:
        dist = np.sqrt((obs["x"] - x)**2 + (obs["z"] - z)**2)
        if dist <= obs["radius"] + 0.2:
            return True
    return False

def move_robot(direction):
    global pose, trajectory
    step = 1
    direction = direction.upper()

    if direction == "W":
        new_x, new_z = pose["x"], pose["z"] + step
        pose["angle"] = 90
    elif direction == "S":
        new_x, new_z = pose["x"], pose["z"] - step
        pose["angle"] = -90
    elif direction == "A":
        new_x, new_z = pose["x"] - step, pose["z"]
        pose["angle"] = 180
    elif direction == "D":
        new_x, new_z = pose["x"] + step, pose["z"]
        pose["angle"] = 0
    else:
        return render_env(), render_slam_map(), None, "❌ Invalid Key"

    if check_collision(new_x, new_z):
        return render_env(), render_slam_map(), "collision.mp3", "🚫 Collision detected!"

    pose["x"], pose["z"] = new_x, new_z
    if noise_enabled:
        noisy_x = pose["x"] + random.uniform(-0.1, 0.1)
        noisy_z = pose["z"] + random.uniform(-0.1, 0.1)
        trajectory.append((noisy_x, noisy_z))
    else:
        trajectory.append((pose["x"], pose["z"]))

    return render_env(), render_slam_map(), None, "Moved " + direction

def render_env():
    global obstacle_hits
    fig, ax = plt.subplots()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_title("SLAM Environment View")

    try:
        bg = mpimg.imread("map.png")
        ax.imshow(bg, extent=(-10, 10, -10, 10), alpha=0.2, zorder=0)
    except:
        pass

    for obs in obstacles:
        circ = plt.Circle((obs["x"], obs["z"]), obs["radius"], color="gray", alpha=0.6)
        ax.add_patch(circ)

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

def handle_text_input(direction):
    return move_robot(direction.strip().upper())

def set_mode(new_mode):
    global mode
    mode = new_mode
    return f"Mode set to: {mode}"

def auto_move_thread():
    global auto_running
    directions = ["W", "A", "S", "D"]
    while auto_running:
        random.shuffle(directions)
        moved = False
        for dir in directions:
            step = 1
            if dir == "W":
                new_x, new_z = pose["x"], pose["z"] + step
            elif dir == "S":
                new_x, new_z = pose["x"], pose["z"] - step
            elif dir == "A":
                new_x, new_z = pose["x"] - step, pose["z"]
            elif dir == "D":
                new_x, new_z = pose["x"] + step, pose["z"]

            if not check_collision(new_x, new_z):
                move_robot(dir)
                moved = True
                break
        if not moved:
            auto_running = False
        time.sleep(1)

def start_auto():
    global auto_running
    if mode != "Automatic":
        return "❗ Switch to 'Automatic' mode first."
    if auto_running:
        return "Auto already running."
    auto_running = True
    threading.Thread(target=auto_move_thread, daemon=True).start()
    return "▶️ Auto started."

def get_state():
    return render_env(), render_slam_map(), None, "Auto Running" if auto_running else "Idle"

with gr.Blocks() as demo:
    gr.Markdown("## 🤖 SLAM: Manual + Automatic Robot Navigation")

    obstacle_slider = gr.Slider(1, 20, value=10, step=1, label="Number of Obstacles")

    direction_input = gr.Textbox(label="Type W / A / S / D", placeholder="W")
    status_text = gr.Textbox(label="Status")
    collision_audio = gr.Audio(label="Collision Sound", interactive=False)

    with gr.Row():
        with gr.Column():
            env_plot = gr.Plot(label="Robot View")
        with gr.Column():
            slam_plot = gr.Plot(label="SLAM Map")

    with gr.Row():
        w = gr.Button("⬆️ W")
        a = gr.Button("⬅️ A")
        s = gr.Button("⬇️ S")
        d = gr.Button("➡️ D")
        reset = gr.Button("🔄 Reset")
        toggle = gr.Button("🔀 Toggle Noise")

    with gr.Row():
        mode_selector = gr.Dropdown(["Manual", "Automatic"], value="Manual", label="Mode")
        start_auto_btn = gr.Button("▶️ Start Auto")

    poll = gr.Button("⏱️ Refresh View", visible=False).every(1000, get_state, outputs=[env_plot, slam_plot, collision_audio, status_text])

    w.click(fn=move_robot, inputs=gr.State("W"), outputs=[env_plot, slam_plot, collision_audio, status_text])
    a.click(fn=move_robot, inputs=gr.State("A"), outputs=[env_plot, slam_plot, collision_audio, status_text])
    s.click(fn=move_robot, inputs=gr.State("S"), outputs=[env_plot, slam_plot, collision_audio, status_text])
    d.click(fn=move_robot, inputs=gr.State("D"), outputs=[env_plot, slam_plot, collision_audio, status_text])
    reset.click(fn=reset_sim, inputs=[obstacle_slider], outputs=[env_plot, slam_plot, collision_audio, status_text])
    toggle.click(fn=lambda: (None, None, None, toggle_noise()), outputs=[env_plot, slam_plot, collision_audio, status_text])
    direction_input.submit(fn=handle_text_input, inputs=direction_input, outputs=[env_plot, slam_plot, collision_audio, status_text])

    mode_selector.change(fn=set_mode, inputs=mode_selector, outputs=status_text)
    start_auto_btn.click(fn=start_auto, outputs=status_text)

demo.launch()
