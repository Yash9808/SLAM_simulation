import gradio as gr
from pythreejs import *
import matplotlib.pyplot as plt

pose = {"x": 0, "y": 0, "z": 0}
trajectory = [(0, 0)]  # Keep track of SLAM path

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
    return render_scene(), render_map()

def render_scene():
    robot = Mesh(
        geometry=BoxGeometry(1, 1, 1),
        material=MeshStandardMaterial(color='red'),
        position=[pose["x"], pose["y"], pose["z"]]
    )
    ambient_light = AmbientLight(color='#ffffff', intensity=0.5)
    directional_light = DirectionalLight(color='white', position=[5, 5, 5], intensity=0.6)
    scene = Scene(children=[robot, ambient_light, directional_light])
    camera = PerspectiveCamera(position=[5, 5, 5])
    camera.lookAt([0, 0, 0])
    renderer = Renderer(scene=scene, camera=camera,
                        controls=[OrbitControls(controlling=camera)],
                        width=400, height=300)
    return renderer

def render_map():
    x_vals = [x for x, z in trajectory]
    z_vals = [z for x, z in trajectory]
    fig, ax = plt.subplots()
    ax.plot(x_vals, z_vals, marker='o', color='blue')
    ax.set_title("SLAM Path (Top-Down)")
    ax.set_xlabel("X Position")
    ax.set_ylabel("Z Position")
    ax.grid(True)
    return fig

with gr.Blocks() as demo:
    gr.Markdown("## 🤖 3D Robot + 🗺️ SLAM Path Visualization")

    with gr.Row():
        with gr.Column():
            scene_display = gr.Component()
        with gr.Column():
            map_display = gr.Plot()

    with gr.Row():
        w_btn = gr.Button("⬆️ W")
        s_btn = gr.Button("⬇️ S")
        a_btn = gr.Button("⬅️ A")
        d_btn = gr.Button("➡️ D")

    w_btn.click(lambda: move_robot("W"), outputs=[scene_display, map_display])
    s_btn.click(lambda: move_robot("S"), outputs=[scene_display, map_display])
    a_btn.click(lambda: move_robot("A"), outputs=[scene_display, map_display])
    d_btn.click(lambda: move_robot("D"), outputs=[scene_display, map_display])

    scene_display.render(render_scene())
    map_display.render(render_map())

demo.launch()
