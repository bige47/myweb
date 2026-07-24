import bpy
import math
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "artifacts" / "warm_white_glossy_orange_peel.blend"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# ----------------------------
# Material: warm white glossy molded coating
# ----------------------------
mat = bpy.data.materials.new("暖白高光细橘皮材质_WarmWhiteGlossy")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

out = nodes.new("ShaderNodeOutputMaterial")
out.name = "材质输出"
out.label = "材质输出"
out.location = (760, 0)

bsdf = nodes.new("ShaderNodeBsdfPrincipled")
bsdf.name = "暖白高光主体"
bsdf.label = "暖白高光主体"
bsdf.location = (430, 40)
bsdf.inputs["Base Color"].default_value = (0.83, 0.80, 0.76, 1.0)
bsdf.inputs["Metallic"].default_value = 0.0
bsdf.inputs["Roughness"].default_value = 0.23
bsdf.inputs["IOR"].default_value = 1.47
# Blender 4.x sockets
if "Coat Weight" in bsdf.inputs:
    bsdf.inputs["Coat Weight"].default_value = 0.16
    bsdf.inputs["Coat Roughness"].default_value = 0.10
elif "Clearcoat" in bsdf.inputs:
    bsdf.inputs["Clearcoat"].default_value = 0.16
    bsdf.inputs["Clearcoat Roughness"].default_value = 0.10

texcoord = nodes.new("ShaderNodeTexCoord")
texcoord.name = "物体坐标"
texcoord.label = "物体坐标"
texcoord.location = (-880, 60)

mapping = nodes.new("ShaderNodeMapping")
mapping.name = "颗粒尺寸"
mapping.label = "颗粒尺寸（可调）"
mapping.location = (-680, 60)
mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)

noise = nodes.new("ShaderNodeTexNoise")
noise.name = "细橘皮噪波"
noise.label = "细橘皮噪波"
noise.location = (-460, 80)
noise.noise_dimensions = '3D'
noise.inputs["Scale"].default_value = 220.0
noise.inputs["Detail"].default_value = 5.0
noise.inputs["Roughness"].default_value = 0.62
noise.inputs["Distortion"].default_value = 0.08

ramp = nodes.new("ShaderNodeValToRGB")
ramp.name = "颗粒对比"
ramp.label = "颗粒对比（控制高光衔接）"
ramp.location = (-220, 90)
ramp.color_ramp.elements[0].position = 0.30
ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
ramp.color_ramp.elements[1].position = 0.72
ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

rough_map = nodes.new("ShaderNodeMapRange")
rough_map.name = "粗糙度范围"
rough_map.label = "粗糙度范围 0.18–0.31"
rough_map.location = (30, 160)
rough_map.inputs["From Min"].default_value = 0.0
rough_map.inputs["From Max"].default_value = 1.0
rough_map.inputs["To Min"].default_value = 0.18
rough_map.inputs["To Max"].default_value = 0.31
rough_map.clamp = True

bump = nodes.new("ShaderNodeBump")
bump.name = "极细表面起伏"
bump.label = "极细表面起伏"
bump.location = (180, -130)
bump.inputs["Strength"].default_value = 0.075
bump.inputs["Distance"].default_value = 0.025

links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], rough_map.inputs["Value"])
links.new(rough_map.outputs["Result"], bsdf.inputs["Roughness"])
links.new(ramp.outputs["Color"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

# Organize nodes
frame_surface = nodes.new("NodeFrame")
frame_surface.name = "表面颜色与高光"
frame_surface.label = "表面颜色与高光"
bsdf.parent = frame_surface

frame_micro = nodes.new("NodeFrame")
frame_micro.name = "细橘皮颗粒"
frame_micro.label = "细橘皮颗粒（不要调得太强）"
for node in (texcoord, mapping, noise, ramp, rough_map, bump):
    node.parent = frame_micro

# ----------------------------
# Preview object: rounded capsule-like slab
# ----------------------------
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0.85), scale=(1.45, 0.82, 0.22))
obj = bpy.context.active_object
obj.name = "材质预览_圆角面板"
obj.data.materials.append(mat)

bev = obj.modifiers.new("圆角", 'BEVEL')
bev.width = 0.38
bev.segments = 8
bev.limit_method = 'ANGLE'

subd = obj.modifiers.new("细分", 'SUBSURF')
subd.levels = 2
subd.render_levels = 2
bpy.ops.object.shade_smooth()

# Ground
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "地面"
gmat = bpy.data.materials.new("中性灰地面")
gmat.diffuse_color = (0.16, 0.16, 0.16, 1)
gmat.use_nodes = True
gpbsdf = gmat.node_tree.nodes.get("Principled BSDF")
gpbsdf.inputs["Base Color"].default_value = (0.13, 0.13, 0.13, 1)
gpbsdf.inputs["Roughness"].default_value = 0.72
ground.data.materials.append(gmat)

# Large softboxes emphasize the highlight transition
for name, loc, energy, size in [
    ("主柔光箱", (2.8, -2.6, 4.5), 950.0, 3.2),
    ("侧面轮廓光", (-3.5, 1.8, 2.7), 520.0, 2.3),
    ("顶部补光", (0.0, 2.0, 5.5), 420.0, 2.8),
]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    lamp = bpy.context.active_object
    lamp.name = name
    lamp.data.energy = energy
    lamp.data.shape = 'DISK'
    lamp.data.size = size
    # point toward preview
    direction = obj.location - lamp.location
    lamp.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Camera
bpy.ops.object.camera_add(location=(4.8, -5.8, 3.7))
cam = bpy.context.active_object
cam.name = "预览相机"
cam.data.lens = 58
cam.data.sensor_width = 36
cam.rotation_euler = (obj.location - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# World and render
world = bpy.data.worlds.new("摄影棚环境")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.055, 0.055, 0.055, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38
bpy.context.scene.world = world

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUTPUT.with_suffix('.png'))
scene.render.film_transparent = False
scene.view_settings.look = 'AgX - Medium High Contrast'

# Custom properties as quick instructions
mat["用途"] = "暖白色高光注塑/喷涂表面，带极细橘皮纹"
mat["建议_BaseColor"] = "RGB约 0.83 / 0.80 / 0.76（线性值）"
mat["建议_Roughness"] = "约0.18–0.31，由细噪波控制"
mat["调节提示"] = "颗粒过强时先降低 Bump Strength，再缩小 Roughness 范围"

# Save and render preview
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
bpy.ops.render.render(write_still=True)
print(f"Saved: {OUTPUT}")
