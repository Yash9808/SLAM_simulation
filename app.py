import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import threading
import time
import os

# Environment and robot parameters
env_size = 10
obstacles = [(2, 2), (3, 5), (6, 7), (7, 3), (5, 5)]
robot_position = [0, 0]
auto_mode = False
robot_path = [tuple(robot_position)]

# Collision detection
def check_collision(x, y):
    return (x, y) in obstacles or not (0 <= x < env_size and 0 <= y < env_size)

# Environment rendering
def render_env():
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(0, env_size)
    ax.set_ylim(0, env_size)
    ax.set_xticks(np.arange(0, env_size + 1, 1))
    ax.set_yticks(np.arange(0, env_size + 1, 1))
    ax.grid(True)

    for (ox, oy) in obstacles:
        ax.add_patch(plt.Rectangle((ox, oy), 1, 1, color="red"))

    for i in range(1, len(robot_path)):
        x_values = [robot_path[i - 1][0] + 0.5, robot_path[i][0] + 0.5]
        y_values = [robot_path[i - 1][1] + 0.5, robot_path[i][1] + 0.5]
        ax.plot(x_values, y_values, "b--")

    rx, ry = robot_position
    ax.plot(rx + 0.5, ry + 0.5, "bo", markersize=15)
    ax.set_title("Robot Environment")
    return fig

# SLAM map simulation
def render_slam_map():
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(np.random.rand(env_size, env_size), cmap="gray", origin="lower")
    ax.set_title("Simulated SLAM Map")
    return fig

# Robot movement logic
def move_robot(direction):
    dx, dz = {
        "up": (0, 1),
        "down": (0, -1),
        "left": (-1, 0),
        "right": (1, 0),
    }.get(direction, (0, 0))

    new_x, new_z = robot_position[0] + dx, robot_position[1] + dz

    if check_collision(new_x, new_z):
        sound_path = "collision1.mp3"
        if not os.path.isfile(sound_path):
            sound_path = ""
        return render_env(), render_slam_map(), sound_path, "🚫 Collision Detected!"

    robot_position[0], robot_position[1] = new_x, new_z
    robot_path.append(tuple(robot_position))
    return render_env(), render_slam_map(), None, "✅ Moved " + direction

# Auto movement logic
def auto_movement(env_plot, slam_plot, audio_trigger, status_text):
    global auto_mode
    directions = ["up", "right", "down", "left"]
    i = 0
    while auto_mode:
        direction = directions[i % len(directions)]
        env_img, slam_img, sound_path, status = move_robot(direction)
        env_plot.update(value=env_img)
        slam_plot.update(value=slam_img)
        status_text.update(value=status)

        if sound_path and os.path.isfile(sound_path):
            audio_trigger.play_event(sound_path)

        time.sleep(1)
        i += 1

# Toggle auto mode
def toggle_auto_mode(env_plot, slam_plot, audio_trigger, status_text):
    global auto_mode
    if auto_mode:
        auto_mode = False
        return "⚪ Auto Mode: OFF"
    else:
        auto_mode = True
        thread = threading.Thread(target=auto_movement, args=(env_plot, slam_plot, audio_trigger, status_text))
        thread.daemon = True
        thread.start()
        return "🟢 Auto Mode: ON"

# Reset function
def reset_simulation():
    global robot_position, robot_path, auto_mode
    auto_mode = False
    robot_position = [0, 0]
    robot_path = [tuple(robot_position)]
    return render_env(), render_slam_map(), None, "🔄 Reset Complete"

# Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Robot Environment Navigation")
    with gr.Row():
        env_plot = gr.Plot(label="Environment View")
        slam_plot = gr.Plot(label="SLAM Map View")

    with gr.Row():
        up_btn = gr.Button("⬆️ Up")
        down_btn = gr.Button("⬇️ Down")
        left_btn = gr.Button("⬅️ Left")
        right_btn = gr.Button("➡️ Right")

    with gr.Row():
        auto_btn = gr.Button("🔁 Toggle Auto Mode")
        reset_btn = gr.Button("🔄 Reset")

    status_text = gr.Textbox(label="Status", interactive=False)
    audio_component = gr.Audio(label="Collision Sound", interactive=False, type="filepath")

    class AudioTrigger:
        def __init__(self):
            self.play_event = lambda path: None

    trigger_audio = AudioTrigger()
    trigger_audio.play_event = lambda path: audio_component.update(value=path) if path and os.path.isfile(path) else None

    up_btn.click(fn=lambda: move_robot("up"), outputs=[env_plot, slam_plot, audio_component, status_text])
    down_btn.click(fn=lambda: move_robot("down"), outputs=[env_plot, slam_plot, audio_component, status_text])
    left_btn.click(fn=lambda: move_robot("left"), outputs=[env_plot, slam_plot, audio_component, status_text])
    right_btn.click(fn=lambda: move_robot("right"), outputs=[env_plot, slam_plot, audio_component, status_text])
    auto_btn.click(fn=lambda: toggle_auto_mode(env_plot, slam_plot, trigger_audio, status_text), outputs=auto_btn)
    reset_btn.click(fn=reset_simulation, outputs=[env_plot, slam_plot, audio_component, status_text])

    demo.load(fn=reset_simulation, outputs=[env_plot, slam_plot, audio_component, status_text])

demo.launch()
