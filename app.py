import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import random
import os

# Robot and environment variables
pose = [250, 250, 0]
trajectory = []
obstacles = []
auto_mode = False

def generate_obstacles(num_obstacles=5):
    global obstacles
    obstacles = []
    for _ in range(num_obstacles):
        x = random.randint(50, 450)
        y = random.randint(50, 450)
        w = random.randint(20, 50)
        h = random.randint(20, 50)
        obstacles.append((x, y, w, h))

def check_collision(x, y):
    for (ox, oy, ow, oh) in obstacles:
        if ox <= x <= ox + ow and oy <= y <= oy + oh:
            return True
    return False

def move_robot(direction):
    global pose, trajectory
    dx, dy = 0, 0
    step_size = 10
    if direction == "W":
        dy = -step_size
    elif direction == "S":
        dy = step_size
    elif direction == "A":
        dx = -step_size
    elif direction == "D":
        dx = step_size

    new_x = pose[0] + dx
    new_y = pose[1] + dy

    if check_collision(new_x, new_y):
        return render_env(), render_slam_map(), "collision1.mp3", "🚫 Collision detected!"

    pose[0] = new_x
    pose[1] = new_y
    trajectory.append((pose[0], pose[1]))

    return render_env(), render_slam_map(), None, f"✅ Moved {direction}"

def render_env():
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(0, 500)
    ax.set_ylim(0, 500)
    ax.set_aspect('equal')
    ax.plot(pose[0], pose[1], 'bo', label="Robot")
    if trajectory:
        ax.plot(*zip(*trajectory), 'b--', label="Trajectory")
    for (x, y, w, h) in obstacles:
        ax.add_patch(plt.Rectangle((x, y), w, h, color='red'))
    ax.legend()
    plt.close()
    return fig

def render_slam_map():
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(0, 500)
    ax.set_ylim(0, 500)
    ax.set_aspect('equal')
    ax.plot(pose[0], pose[1], 'go', label="SLAM Robot")
    ax.legend()
    plt.close()
    return fig

def toggle_auto(auto_state):
    return not auto_state, "✅ Auto mode ON" if not auto_state else "❌ Auto mode OFF"

def auto_step(auto_state):
    if auto_state:
        direction = random.choice(["W", "A", "S", "D"])
        return move_robot(direction)
    return render_env(), render_slam_map(), None, "Auto mode is OFF"

# Build Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 SLAM Robot Demo with Auto Mode")
    env_plot = gr.Plot()
    slam_plot = gr.Plot()
    collision_audio = gr.Audio(value=None, type="filepath", label="Collision", interactive=False, visible=False)
    status_text = gr.Textbox(label="Status")

    auto_state = gr.State(False)

    with gr.Row():
        gr.Button("⬆️").click(fn=move_robot, inputs=gr.Textbox(value="W", visible=False), outputs=[env_plot, slam_plot, collision_audio, status_text])
        gr.Button("⬇️").click(fn=move_robot, inputs=gr.Textbox(value="S", visible=False), outputs=[env_plot, slam_plot, collision_audio, status_text])
        gr.Button("⬅️").click(fn=move_robot, inputs=gr.Textbox(value="A", visible=False), outputs=[env_plot, slam_plot, collision_audio, status_text])
        gr.Button("➡️").click(fn=move_robot, inputs=gr.Textbox(value="D", visible=False), outputs=[env_plot, slam_plot, collision_audio, status_text])
        auto_button = gr.Button("Toggle Auto Mode")

    auto_button.click(fn=toggle_auto, inputs=auto_state, outputs=[auto_state, status_text])

    demo.load(fn=auto_step, inputs=auto_state, outputs=[env_plot, slam_plot, collision_audio, status_text], every=1)

    demo.load(fn=lambda: (render_env(), render_slam_map(), None, "✅ Ready"),
              outputs=[env_plot, slam_plot, collision_audio, status_text])

    generate_obstacles()

demo.launch()
