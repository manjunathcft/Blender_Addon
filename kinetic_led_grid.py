bl_info = {
    "name": "Kinetic LED Ceiling System",
    "author": "manManjunath",
    "version": (2, 3, 0),
    "blender": (4, 0, 0),
    "location": "View3D > N Panel > Kinetic LED",
    "description": "LED panel grid/strips with winch control, duplication, and multiple animation presets",
    "category": "Animation",
}

import bpy
import math
import random
# ----------------------------------------------------
# SCENE PROPERTIES
# ----------------------------------------------------
class KineticLEDProperties(bpy.types.PropertyGroup):
    system_mode: bpy.props.EnumProperty(
        name="System Mode",
        description="Choose between grid mode and winch mode",
        items=[
            ('GRID', "Kinetic Grid", "Animate a grid of individual panels"),
            ('WINCH', "Winch Strip", "Animate strips controlled by winches"),
        ],
        default='GRID'
    )
    # Grid settings
    grid_count_x: bpy.props.IntProperty(name="Count X", default=10, min=1, max=100)
    grid_count_y: bpy.props.IntProperty(name="Count Y", default=10, min=1, max=100)
    grid_spacing: bpy.props.FloatProperty(name="Spacing", default=0.26, min=0.01, max=5.0, unit='LENGTH')

    # Strip setup settings
    strip_display_count: bpy.props.IntProperty(name="Display Count", default=10, min=2, max=100,
        description="Number of LED displays in the strip")
    strip_display_size: bpy.props.FloatProperty(name="Display Size", default=0.256, min=0.1, max=1.0, unit='LENGTH',
        description="Size of each LED display (256mm = 0.256m)")
    strip_axis: bpy.props.EnumProperty(
        name="Strip Axis",
        items=[
            ('X', "X Axis", "Strip along X axis"),
            ('Y', "Y Axis", "Strip along Y axis"),
        ],
        default='X'
    )
    strip_gap: bpy.props.FloatProperty(name="Gap", default=0.01, min=0.0, max=0.1, unit='LENGTH',
        description="Gap between displays")
    strip_winch_mode: bpy.props.EnumProperty(
        name="Winch Mode",
        items=[
            ('3_POINT', "3 Point (Center + Corners)", "Winches at center and both ends"),
            ('5_POINT', "5 Point (Center + Quarters)", "Winches at center, quarters, and ends"),
        ],
        default='3_POINT'
    )

    # Strip duplication settings
    strip_duplicate_count: bpy.props.IntProperty(name="Duplicate Count", default=3, min=1, max=50,
        description="Number of strip copies to create")
    strip_duplicate_axis: bpy.props.EnumProperty(
        name="Duplicate Axis",
        items=[
            ('X', "X Axis", "Duplicate along X axis"),
            ('Y', "Y Axis", "Duplicate along Y axis"),
        ],
        default='Y'
    )
    strip_duplicate_spacing: bpy.props.FloatProperty(name="Duplicate Spacing", default=0.5, min=0.1, max=5.0, unit='LENGTH',
        description="Spacing between duplicated strips")

    # Common animation settings
    anim_z_offset: bpy.props.FloatProperty(name="Z Offset", default=0.0, min=-10.0, max=10.0, unit='LENGTH',
        description="Base Z position offset for animations")

    # Wave animation settings
    wave_amplitude: bpy.props.FloatProperty(name="Amplitude", default=0.25, min=0.01, max=2.0)
    wave_speed: bpy.props.FloatProperty(name="Speed", default=2.0, min=0.1, max=500.0)

    # Radial animation settings
    radial_amplitude: bpy.props.FloatProperty(name="Amplitude", default=0.35, min=0.01, max=2.0)
    radial_speed: bpy.props.FloatProperty(name="Speed", default=3.0, min=0.1, max=500.0)

    # Ramp animation settings
    ramp_amplitude: bpy.props.FloatProperty(name="Amplitude", default=0.3, min=0.01, max=2.0)
    ramp_speed: bpy.props.FloatProperty(name="Speed", default=2.0, min=0.1, max=500.0)
    ramp_direction: bpy.props.EnumProperty(
        name="Direction",
        items=[
            ('X', "X Axis", "Ramp along X axis"),
            ('Y', "Y Axis", "Ramp along Y axis"),
            ('XY', "Diagonal", "Ramp diagonally"),
        ],
        default='X'
    )

    # Circular animation settings
    circular_amplitude: bpy.props.FloatProperty(name="Amplitude", default=0.3, min=0.01, max=2.0)
    circular_speed: bpy.props.FloatProperty(name="Speed", default=1.5, min=0.1, max=500.0)
    circular_rings: bpy.props.IntProperty(name="Rings", default=3, min=1, max=10)

    # Chess animation settings
    chess_amplitude: bpy.props.FloatProperty(name="Amplitude", default=0.25, min=0.01, max=2.0)
    chess_speed: bpy.props.FloatProperty(name="Speed", default=1.0, min=0.1, max=500.0)
    chess_cell_size: bpy.props.IntProperty(name="Cell Size", default=2, min=1, max=10)

    # Text animation settings
    text_content: bpy.props.StringProperty(name="Text", default="HI")
    text_amplitude: bpy.props.FloatProperty(name="Amplitude", default=0.4, min=0.01, max=2.0)
    text_scroll: bpy.props.BoolProperty(name="Scroll", default=True)
    text_speed: bpy.props.FloatProperty(name="Speed", default=2.0, min=0.1, max=500.0)

    # Random animation settings
    random_amplitude: bpy.props.FloatProperty(name="Amplitude", default=0.3, min=0.01, max=2.0)
    random_speed: bpy.props.FloatProperty(name="Speed", default=3.0, min=0.1, max=500.0)
    random_seed: bpy.props.IntProperty(name="Seed", default=1, min=1, max=9999)

    # LED Texture settings
    led_texture_type: bpy.props.EnumProperty(
        name="LED Texture Type",
        items=[
            ('SOLID', "Solid Color", "All LEDs show a single color"),
            ('CHECKER', "Checker Pattern", "LEDs show a checkerboard pattern"),
            ('GRADIENT', "Gradient", "LEDs show a gradient pattern"),
            ('WAVE_COLOR', "Wave Pattern", "Animated color waves across panels"),
            ('PULSE', "Pulse Pattern", "Pulsing/breathing color animation"),
            ('RAINBOW', "Rainbow Cycle", "Cycling rainbow colors animation"),
            ('SCAN', "Scan Line", "Scanning line effect across panels"),
            ('NOISE', "Noise Pattern", "Animated noise/static pattern"),
            ('STROBE', "Strobe", "Flashing strobe effect"),
            ('IMAGE', "Image Texture", "Load an image texture (UV checker, etc.)"),
        ],
        default='SOLID'
    )

    # Image texture settings
    texture_image_path: bpy.props.StringProperty(
        name="Image Path",
        description="Path to image texture file",
        subtype='FILE_PATH',
        default=""
    )

    # Unified texture mapping toggle
    unified_texture_mapping: bpy.props.BoolProperty(
        name="Unified Mapping",
        description="Map texture across entire grid as one continuous image instead of per-panel",
        default=True
    )

    # Grid bounds tracking (set automatically when grid/strips are created)
    grid_bounds_min_x: bpy.props.FloatProperty(default=0.0)
    grid_bounds_max_x: bpy.props.FloatProperty(default=1.0)
    grid_bounds_min_y: bpy.props.FloatProperty(default=0.0)
    grid_bounds_max_y: bpy.props.FloatProperty(default=1.0)

    # Statistics
    total_panels_created: bpy.props.IntProperty(name="Total Panels", default=0)
    total_strips_created: bpy.props.IntProperty(name="Total Strips", default=0)
    color1: bpy.props.FloatVectorProperty(name="Color 1", subtype='COLOR', default=(1.0, 0.0, 0.0, 1.0), size=4)
    color2: bpy.props.FloatVectorProperty(name="Color 2", subtype='COLOR', default=(0.0, 0.0, 1.0, 1.0), size=4)
    checker_scale: bpy.props.FloatProperty(name="Checker Scale", default=5.0, min=1.0, max=50.0)
    gradient_axis: bpy.props.EnumProperty(
        name="Gradient Axis",
        items=[
            ('X', "X Axis", "Gradient along X axis"),
            ('Y', "Y Axis", "Gradient along Y axis"),
        ],
        default='X'
    )

    # Animated texture settings
    texture_anim_speed: bpy.props.FloatProperty(
        name="Animation Speed",
        default=1.0,
        min=0.1,
        max=10.0,
        description="Speed of texture animation"
    )
    texture_scale: bpy.props.FloatProperty(
        name="Texture Scale",
        default=2.0,
        min=0.1,
        max=20.0,
        description="Scale of the texture pattern"
    )
    wave_direction: bpy.props.EnumProperty(
        name="Wave Direction",
        items=[
            ('X', "Horizontal", "Wave moves horizontally"),
            ('Y', "Vertical", "Wave moves vertically"),
            ('RADIAL', "Radial", "Wave expands from center"),
        ],
        default='X'
    )
    scan_width: bpy.props.FloatProperty(
        name="Scan Width",
        default=0.2,
        min=0.05,
        max=1.0,
        description="Width of the scanning line"
    )
    emission_strength: bpy.props.FloatProperty(
        name="Emission Strength",
        default=5.0,
        min=0.1,
        max=50.0,
        description="Brightness of LED emission"
    )
    
# ----------------------------------------------------
# UTILITY FUNCTIONS
# ----------------------------------------------------
def get_led_default_material():
    mat_name = "LED_Default_Material"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear existing nodes
    for node in nodes:
        nodes.remove(node)

    # Create nodes
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = 200, 0
    emission_node = nodes.new(type='ShaderNodeEmission')
    emission_node.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0) # Default to black
    emission_node.inputs['Strength'].default_value = 1.0
    emission_node.location = 0, 0

    # Link nodes
    links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])

    return mat

def clear_object_animation(obj):
    """Remove all animation data and drivers from an object's Z location"""
    # Remove drivers on location Z
    obj.driver_remove("location", 2)
    # Clear animation data
    if obj.animation_data:
        obj.animation_data_clear()


def get_strip_winches():
    winches = [obj for obj in bpy.data.objects if "winch_index" in obj]
    strip_winches = {}
    if not winches:
        return strip_winches, 0

    for winch in winches:
        parts = winch.name.split("_")
        strip_key = "0"  # for original strip
        winch_idx = -1
        if len(parts) == 2:  # WINCH_i
            strip_key = "0"
            winch_idx = int(parts[1])
        elif len(parts) == 3:  # WINCH_dup_i
            strip_key = parts[1]
            winch_idx = int(parts[2])

        if strip_key not in strip_winches:
            strip_winches[strip_key] = []
        strip_winches[strip_key].append((winch_idx, winch))

    # Sort by strip index
    sorted_strip_keys = sorted(strip_winches.keys(), key=int)

    sorted_strip_winches = {}
    for key in sorted_strip_keys:
        winch_list = strip_winches[key]
        # Sort by winch index within the strip
        winch_list.sort(key=lambda x: x[0])
        sorted_strip_winches[key] = winch_list

    return sorted_strip_winches, len(winches)


def clear_winch_animation():
    winches = [obj for obj in bpy.data.objects if obj.name.startswith("WINCH_")]
    for winch in winches:
        winch.driver_remove("location", 2)
        if winch.animation_data:
            winch.animation_data_clear()


def animate_panels_from_winches():
    panel_count = 0
    for obj in bpy.data.objects:
        if obj.get("is_strip_panel"):
            clear_object_animation(obj)

            influences_str = obj.get("winch_influences", "[]")
            try:
                influences = eval(influences_str)
            except:
                influences = []

            if not influences:
                continue

            winch_prefix = obj.get("winch_prefix", "")
            
            drv = obj.driver_add("location", 2).driver
            drv.type = 'SCRIPTED'

            expr_parts = []
            total_influence = 0

            for winch_idx, influence in influences:
                if winch_prefix:
                    winch_name = f"WINCH_{winch_prefix}_{winch_idx}"
                else:
                    winch_name = f"WINCH_{winch_idx}"

                var_name = f"w{winch_idx}"
                
                winch_obj = bpy.data.objects.get(winch_name)
                if not winch_obj:
                    # This could happen if a winch was deleted.
                    continue

                var = drv.variables.new()
                var.name = var_name
                var.type = 'TRANSFORMS'
                var.targets[0].id = winch_obj
                var.targets[0].transform_type = 'LOC_Z'
                var.targets[0].transform_space = 'WORLD_SPACE'

                expr_parts.append(f"{var_name}*{influence:.4f}")
                total_influence += influence

            if expr_parts and total_influence > 0:
                drv.expression = f"({'+'.join(expr_parts)})/{total_influence:.4f}"
                panel_count += 1
    return panel_count

# ----------------------------------------------------
# CREATE LED GRID
# ----------------------------------------------------
class KINETIC_OT_create_grid(bpy.types.Operator):
    bl_idname = "kinetic.create_grid"
    bl_label = "Create LED Grid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        panel = context.active_object
        if not panel:
            self.report({'ERROR'}, "Select one LED panel object")
            return {'CANCELLED'}

        grid_coll = bpy.data.collections.new("LED_GRID")
        context.scene.collection.children.link(grid_coll)

        panel_count = 0
        for x in range(props.grid_count_x):
            for y in range(props.grid_count_y):
                inst = panel.copy()
                inst.data = panel.data
                inst.location = (
                    x * props.grid_spacing,
                    y * props.grid_spacing,
                    0
                )
                grid_coll.objects.link(inst)

                # Assign default material
                if inst.data.materials:
                    inst.data.materials[0] = get_led_default_material()
                else:
                    inst.data.materials.append(get_led_default_material())
                panel_count += 1

        # Store grid bounds for unified texture mapping
        props.grid_bounds_min_x = 0.0
        props.grid_bounds_max_x = (props.grid_count_x - 1) * props.grid_spacing
        props.grid_bounds_min_y = 0.0
        props.grid_bounds_max_y = (props.grid_count_y - 1) * props.grid_spacing
        props.total_panels_created = panel_count
        props.total_strips_created = 0

        self.report({'INFO'}, f"Created LED Grid: {props.grid_count_x}x{props.grid_count_y} = {panel_count} panels")
        return {'FINISHED'}

# ----------------------------------------------------
# CREATE LED STRIP WITH WINCHES
# ----------------------------------------------------
class KINETIC_OT_create_strip(bpy.types.Operator):
    bl_idname = "kinetic.create_strip"
    bl_label = "Create LED Strip"
    bl_description = "Create LED strip with winch control points at center and corners"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        panel = context.active_object
        if not panel:
            self.report({'ERROR'}, "Select one LED panel object")
            return {'CANCELLED'}

        # Create collection
        strip_coll = bpy.data.collections.new("LED_STRIP")
        context.scene.collection.children.link(strip_coll)

        # Calculate spacing
        display_size = props.strip_display_size
        gap = props.strip_gap
        total_spacing = display_size + gap
        count = props.strip_display_count
        total_length = (count - 1) * total_spacing

        # Determine axis
        is_x_axis = props.strip_axis == 'X'

        # Create winch points based on mode
        winch_positions = []
        if props.strip_winch_mode == '3_POINT':
            # Start, Center, End
            winch_positions = [0, total_length / 2, total_length]
        else:  # 5_POINT
            # Start, Quarter, Center, Three-Quarter, End
            winch_positions = [0, total_length / 4, total_length / 2,
                              3 * total_length / 4, total_length]

        # Create winch empties
        winches = []
        for i, pos in enumerate(winch_positions):
            winch = bpy.data.objects.new(f"WINCH_{i}", None)
            winch.empty_display_type = 'SPHERE'
            winch.empty_display_size = 0.1
            if is_x_axis:
                winch.location = (pos, 0, 0)
            else:
                winch.location = (0, pos, 0)
            # Store strip info on winch
            winch["strip_collection"] = strip_coll.name
            winch["winch_index"] = i
            winch["winch_position"] = pos
            winch["total_length"] = total_length
            strip_coll.objects.link(winch)
            winches.append(winch)

        # Create LED panels with custom properties for winch relationship
        panels = []
        for i in range(count):
            inst = panel.copy()
            inst.data = panel.data
            pos = i * total_spacing

            if is_x_axis:
                inst.location = (pos, 0, 0)
            else:
                inst.location = (0, pos, 0)

            # Store panel metadata for animation
            inst["is_strip_panel"] = True
            inst["panel_position"] = pos
            inst["total_length"] = total_length
            inst["strip_collection"] = strip_coll.name

            # Calculate influence weights for each winch
            norm_pos = pos / total_length if total_length > 0 else 0
            influence_data = []
            for j, winch_pos in enumerate(winch_positions):
                winch_norm = winch_pos / total_length if total_length > 0 else 0
                distance = abs(norm_pos - winch_norm)
                max_dist = 1.0 / (len(winch_positions) - 1) if len(winch_positions) > 1 else 1.0
                if distance <= max_dist:
                    influence = 1.0 - (distance / max_dist)
                    influence_data.append((j, influence))

            # Store influence data as JSON string
            inst["winch_influences"] = str(influence_data)

            strip_coll.objects.link(inst)
            panels.append(inst)

            # Assign default material
            if inst.data.materials:
                inst.data.materials[0] = get_led_default_material()
            else:
                inst.data.materials.append(get_led_default_material())

        # Store bounds for unified texture mapping
        if is_x_axis:
            props.grid_bounds_min_x = 0.0
            props.grid_bounds_max_x = total_length
            props.grid_bounds_min_y = 0.0
            props.grid_bounds_max_y = 0.0
        else:
            props.grid_bounds_min_x = 0.0
            props.grid_bounds_max_x = 0.0
            props.grid_bounds_min_y = 0.0
            props.grid_bounds_max_y = total_length

        props.total_panels_created = count
        props.total_strips_created = 1

        self.report({'INFO'}, f"Created strip with {count} displays and {len(winches)} winches")
        return {'FINISHED'}

# ----------------------------------------------------
# DUPLICATE STRIP
# ----------------------------------------------------
class KINETIC_OT_duplicate_strip(bpy.types.Operator):
    bl_idname = "kinetic.duplicate_strip"
    bl_label = "Duplicate Strip"
    bl_description = "Duplicate LED strip along an axis"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led

        # Find existing LED_STRIP collections
        strip_colls = [c for c in bpy.data.collections if c.name.startswith("LED_STRIP")]
        if not strip_colls:
            self.report({'ERROR'}, "No LED strip found. Create a strip first.")
            return {'CANCELLED'}

        # Get the first strip collection as source
        source_coll = strip_colls[0]

        # Calculate offset based on strip axis and duplicate axis
        is_strip_x = props.strip_axis == 'X'
        is_dup_x = props.strip_duplicate_axis == 'X'

        # Get bounds of existing strip
        all_objects = list(source_coll.objects)
        if not all_objects:
            self.report({'ERROR'}, "Strip collection is empty.")
            return {'CANCELLED'}

        # Get source strip bounds
        xs = [obj.location.x for obj in all_objects]
        ys = [obj.location.y for obj in all_objects]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Calculate strip dimensions
        strip_width_x = max_x - min_x
        strip_width_y = max_y - min_y

        total_duplicated = 0

        for dup_idx in range(1, props.strip_duplicate_count + 1):
            # Calculate offset for this duplicate
            if is_dup_x:
                offset_x = dup_idx * (strip_width_x + props.strip_duplicate_spacing) if is_strip_x else dup_idx * props.strip_duplicate_spacing
                offset_y = 0 if is_strip_x else dup_idx * props.strip_duplicate_spacing
            else:
                offset_x = 0 if is_strip_x else dup_idx * props.strip_duplicate_spacing
                offset_y = dup_idx * (strip_width_y + props.strip_duplicate_spacing) if not is_strip_x else dup_idx * props.strip_duplicate_spacing

            # Create new collection for this duplicate
            new_coll = bpy.data.collections.new(f"LED_STRIP_{dup_idx}")
            context.scene.collection.children.link(new_coll)

            # Create mapping from old winch names to new
            winch_mapping = {}

            # First duplicate winches
            for obj in source_coll.objects:
                if obj.name.startswith("WINCH_"):
                    new_obj = obj.copy()
                    new_obj.location = (
                        obj.location.x + offset_x,
                        obj.location.y + offset_y,
                        obj.location.z
                    )
                    # Update winch name to avoid conflicts
                    old_idx = obj.name.split("_")[1]
                    new_obj.name = f"WINCH_{dup_idx}_{old_idx}"
                    new_obj["strip_collection"] = new_coll.name
                    new_coll.objects.link(new_obj)
                    winch_mapping[obj.name] = new_obj.name
                    total_duplicated += 1

            # Then duplicate panels
            for obj in source_coll.objects:
                if obj.get("is_strip_panel"):
                    new_obj = obj.copy()
                    new_obj.data = obj.data
                    new_obj.location = (
                        obj.location.x + offset_x,
                        obj.location.y + offset_y,
                        obj.location.z
                    )
                    new_obj["strip_collection"] = new_coll.name

                    # Update winch influences to point to new winches
                    influences_str = obj.get("winch_influences", "[]")
                    try:
                        influences = eval(influences_str)
                        # Update winch indices for the new set
                        new_influences = [(int(f"{dup_idx}{idx}"), inf) for idx, inf in influences]
                        new_obj["winch_influences"] = str(influences)  # Keep original indices
                        new_obj["winch_prefix"] = f"{dup_idx}"
                    except:
                        pass

                    new_coll.objects.link(new_obj)
                    total_duplicated += 1

        # Update bounds to include all strips
        all_strip_colls = [c for c in bpy.data.collections if c.name.startswith("LED_STRIP")]
        all_positions = []
        panel_count = 0
        for coll in all_strip_colls:
            for obj in coll.objects:
                if obj.get("is_strip_panel"):
                    all_positions.append((obj.location.x, obj.location.y))
                    panel_count += 1

        if all_positions:
            props.grid_bounds_min_x = min(p[0] for p in all_positions)
            props.grid_bounds_max_x = max(p[0] for p in all_positions)
            props.grid_bounds_min_y = min(p[1] for p in all_positions)
            props.grid_bounds_max_y = max(p[1] for p in all_positions)

        props.total_panels_created = panel_count
        props.total_strips_created = len(all_strip_colls)

        self.report({'INFO'}, f"Created {props.strip_duplicate_count} duplicate strips | Total: {props.total_strips_created} strips, {panel_count} panels")
        return {'FINISHED'}


# ----------------------------------------------------
# WINCH WAVE ANIMATION
# ----------------------------------------------------
class KINETIC_OT_winch_wave(bpy.types.Operator):
    bl_idname = "kinetic.winch_wave"
    bl_label = "Wave Pattern"
    bl_description = "Wave animation pattern for winch strips"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found. Create a strip first.")
            return {'CANCELLED'}

        clear_winch_animation()

        for strip_idx, (strip_key, winch_list) in enumerate(strip_winches.items()):
            for i, (winch_idx, winch) in enumerate(winch_list):
                drv = winch.driver_add("location", 2).driver
                phase = i * 0.5 + strip_idx * 0.3
                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"sin(frame/{props.wave_speed} + {phase}) * {props.wave_amplitude}"
                )

        panel_count = animate_panels_from_winches()
        self.report({'INFO'}, f"Animated {total_winches} winches and {panel_count} panels with Wave pattern")
        return {'FINISHED'}


# ----------------------------------------------------
# WINCH RADIAL ANIMATION
# ----------------------------------------------------
class KINETIC_OT_winch_radial(bpy.types.Operator):
    bl_idname = "kinetic.winch_radial"
    bl_label = "Radial Pattern"
    bl_description = "Radial animation pattern for winch strips"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found.")
            return {'CANCELLED'}

        clear_winch_animation()

        # Calculate center of all winches
        all_positions = []
        for strip_key, winch_list in strip_winches.items():
            for winch_idx, winch in winch_list:
                all_positions.append((winch.location.x, winch.location.y))

        if all_positions:
            center_x = sum(p[0] for p in all_positions) / len(all_positions)
            center_y = sum(p[1] for p in all_positions) / len(all_positions)
        else:
            center_x, center_y = 0, 0

        for strip_idx, (strip_key, winch_list) in enumerate(strip_winches.items()):
            for i, (winch_idx, winch) in enumerate(winch_list):
                drv = winch.driver_add("location", 2).driver
                rel_x = winch.location.x - center_x
                rel_y = winch.location.y - center_y
                dist = math.sqrt(rel_x**2 + rel_y**2)
                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"sin(frame/{props.radial_speed} + {dist}) * {props.radial_amplitude}"
                )

        panel_count = animate_panels_from_winches()
        self.report({'INFO'}, f"Animated {total_winches} winches and {panel_count} panels with Radial pattern")
        return {'FINISHED'}


# ----------------------------------------------------
# WINCH RAMP ANIMATION
# ----------------------------------------------------
class KINETIC_OT_winch_ramp(bpy.types.Operator):
    bl_idname = "kinetic.winch_ramp"
    bl_label = "Ramp Pattern"
    bl_description = "Ramp animation pattern for winch strips"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found.")
            return {'CANCELLED'}

        clear_winch_animation()

        for strip_idx, (strip_key, winch_list) in enumerate(strip_winches.items()):
            for i, (winch_idx, winch) in enumerate(winch_list):
                drv = winch.driver_add("location", 2).driver

                if props.ramp_direction == 'X':
                    pos_val = winch.location.x + strip_idx * 0.5
                elif props.ramp_direction == 'Y':
                    pos_val = winch.location.y + strip_idx * 0.5
                else:  # XY diagonal
                    pos_val = winch.location.x + winch.location.y + strip_idx * 0.5

                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"((sin(frame/{props.ramp_speed} + {pos_val}*0.5) + 1) / 2) * {props.ramp_amplitude}"
                )

        panel_count = animate_panels_from_winches()
        self.report({'INFO'}, f"Animated {total_winches} winches and {panel_count} panels with Ramp pattern")
        return {'FINISHED'}


# ----------------------------------------------------
# WINCH CIRCULAR ANIMATION
# ----------------------------------------------------
class KINETIC_OT_winch_circular(bpy.types.Operator):
    bl_idname = "kinetic.winch_circular"
    bl_label = "Circular Pattern"
    bl_description = "Circular animation pattern for winch strips"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found.")
            return {'CANCELLED'}

        clear_winch_animation()

        # Calculate center of all winches
        all_positions = []
        for strip_key, winch_list in strip_winches.items():
            for winch_idx, winch in winch_list:
                all_positions.append((winch.location.x, winch.location.y))

        if all_positions:
            center_x = sum(p[0] for p in all_positions) / len(all_positions)
            center_y = sum(p[1] for p in all_positions) / len(all_positions)
        else:
            center_x, center_y = 0, 0

        for strip_idx, (strip_key, winch_list) in enumerate(strip_winches.items()):
            for i, (winch_idx, winch) in enumerate(winch_list):
                drv = winch.driver_add("location", 2).driver
                rel_x = winch.location.x - center_x
                rel_y = winch.location.y - center_y
                angle = math.atan2(rel_y, rel_x)
                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"sin(frame/{props.circular_speed} + {angle} * {props.circular_rings}) * {props.circular_amplitude}"
                )

        panel_count = animate_panels_from_winches()
        self.report({'INFO'}, f"Animated {total_winches} winches and {panel_count} panels with Circular pattern")
        return {'FINISHED'}

# ----------------------------------------------------
# WINCH RANDOM ANIMATION
# ----------------------------------------------------
class KINETIC_OT_winch_random(bpy.types.Operator):
    bl_idname = "kinetic.winch_random"
    bl_label = "Random Pattern"
    bl_description = "Random animation pattern for winch strips"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found.")
            return {'CANCELLED'}

        clear_winch_animation()
        random.seed(props.random_seed)

        for strip_idx, (strip_key, winch_list) in enumerate(strip_winches.items()):
            for i, (winch_idx, winch) in enumerate(winch_list):
                drv = winch.driver_add("location", 2).driver
                phase = random.uniform(0, 6.28)
                freq_mult = random.uniform(0.5, 1.5)
                amp_mult = random.uniform(0.7, 1.3)

                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"sin(frame/{props.random_speed * freq_mult} + {phase}) * {props.random_amplitude * amp_mult}"
                )

        panel_count = animate_panels_from_winches()
        self.report({'INFO'}, f"Animated {total_winches} winches and {panel_count} panels with Random pattern")
        return {'FINISHED'}


# ----------------------------------------------------
# WAVE ANIMATION
# ----------------------------------------------------
class KINETIC_OT_wave_animation(bpy.types.Operator):
    bl_idname = "kinetic.wave_animation"
    bl_label = "Apply Wave Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        for obj in context.selected_objects:
            # Clear previous animation
            clear_object_animation(obj)
            # Apply new driver
            drv = obj.driver_add("location", 2).driver
            drv.expression = (
                f"{props.anim_z_offset} + sin(frame/{props.wave_speed} + "
                f"({obj.location.x} + {obj.location.y})*2) * {props.wave_amplitude}"
            )
        return {'FINISHED'}

# ----------------------------------------------------
# RADIAL ANIMATION
# ----------------------------------------------------
class KINETIC_OT_radial_animation(bpy.types.Operator):
    bl_idname = "kinetic.radial_animation"
    bl_label = "Apply Radial Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        for obj in context.selected_objects:
            # Clear previous animation
            clear_object_animation(obj)
            # Apply new driver
            drv = obj.driver_add("location", 2).driver
            drv.expression = (
                f"{props.anim_z_offset} + sin(frame/{props.radial_speed} + "
                f"sqrt({obj.location.x}**2 + {obj.location.y}**2)) * {props.radial_amplitude}"
            )
        return {'FINISHED'}

# ----------------------------------------------------
# RAMP ANIMATION
# ----------------------------------------------------
class KINETIC_OT_ramp_animation(bpy.types.Operator):
    bl_idname = "kinetic.ramp_animation"
    bl_label = "Apply Ramp Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        for obj in context.selected_objects:
            clear_object_animation(obj)
            drv = obj.driver_add("location", 2).driver

            if props.ramp_direction == 'X':
                pos_expr = f"{obj.location.x}"
            elif props.ramp_direction == 'Y':
                pos_expr = f"{obj.location.y}"
            else:  # XY diagonal
                pos_expr = f"({obj.location.x} + {obj.location.y})"

            drv.expression = (
                f"{props.anim_z_offset} + "
                f"((sin(frame/{props.ramp_speed} + {pos_expr}*0.5) + 1) / 2) * {props.ramp_amplitude}"
            )
        return {'FINISHED'}

# ----------------------------------------------------
# CIRCULAR ANIMATION
# ----------------------------------------------------
class KINETIC_OT_circular_animation(bpy.types.Operator):
    bl_idname = "kinetic.circular_animation"
    bl_label = "Apply Circular Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        for obj in context.selected_objects:
            clear_object_animation(obj)
            drv = obj.driver_add("location", 2).driver
            # Rotating circular pattern with multiple rings
            drv.expression = (
                f"{props.anim_z_offset} + "
                f"sin(frame/{props.circular_speed} + "
                f"atan2({obj.location.y}, {obj.location.x}) * {props.circular_rings}) * {props.circular_amplitude}"
            )
        return {'FINISHED'}

# ----------------------------------------------------
# CHESS ANIMATION
# ----------------------------------------------------
class KINETIC_OT_chess_animation(bpy.types.Operator):
    bl_idname = "kinetic.chess_animation"
    bl_label = "Apply Chess Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        selected = list(context.selected_objects)
        if not selected:
            return {'CANCELLED'}

        # Get grid bounds
        xs = [obj.location.x for obj in selected]
        ys = [obj.location.y for obj in selected]
        min_x, min_y = min(xs), min(ys)
        spacing = props.grid_spacing if props.grid_spacing > 0 else 0.26

        for obj in selected:
            clear_object_animation(obj)
            # Calculate grid position
            grid_x = int(round((obj.location.x - min_x) / spacing))
            grid_y = int(round((obj.location.y - min_y) / spacing))
            # Chess pattern: alternating cells
            cell_x = grid_x // props.chess_cell_size
            cell_y = grid_y // props.chess_cell_size
            is_white = (cell_x + cell_y) % 2

            drv = obj.driver_add("location", 2).driver
            # Alternating up/down based on chess pattern
            if is_white:
                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"sin(frame/{props.chess_speed}) * {props.chess_amplitude}"
                )
            else:
                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"sin(frame/{props.chess_speed} + 3.14159) * {props.chess_amplitude}"
                )
        return {'FINISHED'}

# ----------------------------------------------------
# TEXT ANIMATION
# ----------------------------------------------------
# Simple 5x3 pixel font for basic characters
PIXEL_FONT = {
    'A': ["111", "101", "111", "101", "101"],
    'B': ["110", "101", "110", "101", "110"],
    'C': ["111", "100", "100", "100", "111"],
    'D': ["110", "101", "101", "101", "110"],
    'E': ["111", "100", "110", "100", "111"],
    'F': ["111", "100", "110", "100", "100"],
    'G': ["111", "100", "101", "101", "111"],
    'H': ["101", "101", "111", "101", "101"],
    'I': ["111", "010", "010", "010", "111"],
    'J': ["011", "001", "001", "101", "111"],
    'K': ["101", "110", "100", "110", "101"],
    'L': ["100", "100", "100", "100", "111"],
    'M': ["101", "111", "101", "101", "101"],
    'N': ["101", "111", "111", "101", "101"],
    'O': ["111", "101", "101", "101", "111"],
    'P': ["111", "101", "111", "100", "100"],
    'Q': ["111", "101", "101", "111", "001"],
    'R': ["111", "101", "110", "101", "101"],
    'S': ["111", "100", "111", "001", "111"],
    'T': ["111", "010", "010", "010", "010"],
    'U': ["101", "101", "101", "101", "111"],
    'V': ["101", "101", "101", "101", "010"],
    'W': ["101", "101", "101", "111", "101"],
    'X': ["101", "101", "010", "101", "101"],
    'Y': ["101", "101", "010", "010", "010"],
    'Z': ["111", "001", "010", "100", "111"],
    '0': ["111", "101", "101", "101", "111"],
    '1': ["010", "110", "010", "010", "111"],
    '2': ["111", "001", "111", "100", "111"],
    '3': ["111", "001", "111", "001", "111"],
    '4': ["101", "101", "111", "001", "001"],
    '5': ["111", "100", "111", "001", "111"],
    '6': ["111", "100", "111", "101", "111"],
    '7': ["111", "001", "001", "001", "001"],
    '8': ["111", "101", "111", "101", "111"],
    '9': ["111", "101", "111", "001", "111"],
    ' ': ["000", "000", "000", "000", "000"],
    '!': ["010", "010", "010", "000", "010"],
    '-': ["000", "000", "111", "000", "000"],
}

class KINETIC_OT_text_animation(bpy.types.Operator):
    bl_idname = "kinetic.text_animation"
    bl_label = "Apply Text Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        selected = list(context.selected_objects)
        if not selected:
            return {'CANCELLED'}

        # Get grid bounds
        xs = [obj.location.x for obj in selected]
        ys = [obj.location.y for obj in selected]
        min_x, min_y = min(xs), min(ys)
        max_x, max_y = max(ys), max(ys)
        spacing = props.grid_spacing if props.grid_spacing > 0 else 0.26

        grid_width = int(round((max_x - min_x) / spacing)) + 1
        grid_height = int(round((max_y - min_y) / spacing)) + 1

        # Build text bitmap
        text = props.text_content.upper()
        text_width = len(text) * 4  # 3 pixels + 1 space per char

        for obj in selected:
            clear_object_animation(obj)
            grid_x = int(round((obj.location.x - min_x) / spacing))
            grid_y = int(round((obj.location.y - min_y) / spacing))

            drv = obj.driver_add("location", 2).driver

            if props.text_scroll:
                # Scrolling text expression
                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"(sin(frame/{props.text_speed} + {grid_x}*0.5 + {grid_y}*0.3) > 0.5) * {props.text_amplitude}"
                )
            else:
                # Static text - check if this pixel should be on
                char_idx = grid_x // 4
                char_x = grid_x % 4
                char_y = grid_height - 1 - grid_y  # Flip Y

                is_on = 0
                if char_idx < len(text) and char_x < 3 and 0 <= char_y < 5:
                    char = text[char_idx]
                    if char in PIXEL_FONT:
                        row = PIXEL_FONT[char][char_y] if char_y < len(PIXEL_FONT[char]) else "000"
                        is_on = 1 if char_x < len(row) and row[char_x] == '1' else 0

                if is_on:
                    drv.expression = (
                        f"{props.anim_z_offset} + "
                        f"abs(sin(frame/{props.text_speed})) * {props.text_amplitude}"
                    )
                else:
                    drv.expression = f"{props.anim_z_offset}"

        return {'FINISHED'}

# ----------------------------------------------------
# RANDOM ANIMATION
# ----------------------------------------------------
class KINETIC_OT_random_animation(bpy.types.Operator):
    bl_idname = "kinetic.random_animation"
    bl_label = "Apply Random Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        random.seed(props.random_seed)

        for obj in context.selected_objects:
            clear_object_animation(obj)
            drv = obj.driver_add("location", 2).driver
            # Random phase and frequency variation per object
            phase = random.uniform(0, 6.28)
            freq_mult = random.uniform(0.5, 1.5)
            amp_mult = random.uniform(0.7, 1.3)

            drv.expression = (
                f"{props.anim_z_offset} + "
                f"sin(frame/{props.random_speed * freq_mult} + {phase}) * {props.random_amplitude * amp_mult}"
            )
        return {'FINISHED'}

class KINETIC_OT_apply_led_texture(bpy.types.Operator):
    bl_idname = "kinetic.apply_led_texture"
    bl_label = "Apply LED Texture"
    bl_description = "Apply texture mapped across the entire LED grid using world positions"
    bl_options = {'REGISTER', 'UNDO'}

    def create_animated_material(self, context, props, mat_name, min_x, max_x, min_y, max_y):
        """Create or update an animated material using Object Info for world position mapping"""
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
            nodes = mat.node_tree.nodes
            for node in nodes:
                nodes.remove(node)
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            for node in nodes:
                nodes.remove(node)

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Output node
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = 800, 0

        # Emission Shader
        emission_node = nodes.new(type='ShaderNodeEmission')
        emission_node.inputs['Strength'].default_value = props.emission_strength
        emission_node.location = 600, 0
        links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])

        # For unified mapping, use Object Info node to get actual world position of each LED
        if props.unified_texture_mapping:
            # Object Info node - gives actual world location of each object instance
            obj_info = nodes.new(type='ShaderNodeObjectInfo')
            obj_info.name = 'LED_Position_Info'
            obj_info.location = -800, 0

            # Separate XYZ to split the location vector
            separate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
            separate_xyz.name = 'Split_Coords'
            separate_xyz.location = -600, 0
            links.new(obj_info.outputs['Location'], separate_xyz.inputs['Vector'])

            # Map Range X - converts world X to 0-1 texture space
            map_x = nodes.new(type='ShaderNodeMapRange')
            map_x.name = 'Map_X'
            map_x.location = -400, 100
            map_x.inputs[1].default_value = min_x  # From Min
            map_x.inputs[2].default_value = max_x  # From Max
            map_x.inputs[3].default_value = 0.0    # To Min
            map_x.inputs[4].default_value = 1.0    # To Max
            links.new(separate_xyz.outputs['X'], map_x.inputs['Value'])

            # Map Range Y - converts world Y to 0-1 texture space
            map_y = nodes.new(type='ShaderNodeMapRange')
            map_y.name = 'Map_Y'
            map_y.location = -400, -100
            map_y.inputs[1].default_value = min_y  # From Min
            map_y.inputs[2].default_value = max_y  # From Max
            map_y.inputs[3].default_value = 0.0    # To Min
            map_y.inputs[4].default_value = 1.0    # To Max
            links.new(separate_xyz.outputs['Y'], map_y.inputs['Value'])

            # Combine XYZ - combine X and Y back into a vector for the texture
            combine_xyz = nodes.new(type='ShaderNodeCombineXYZ')
            combine_xyz.name = 'Texture_Vector'
            combine_xyz.location = -200, 0
            links.new(map_x.outputs['Result'], combine_xyz.inputs['X'])
            links.new(map_y.outputs['Result'], combine_xyz.inputs['Y'])
            combine_xyz.inputs['Z'].default_value = 0.0

            # Mapping node for additional control (scale, rotation, offset)
            mapping_node = nodes.new(type='ShaderNodeMapping')
            mapping_node.location = 0, 0
            links.new(combine_xyz.outputs['Vector'], mapping_node.inputs['Vector'])
        else:
            # Per-object mapping (original behavior using texture coordinates)
            tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
            tex_coord_node.location = -400, 0
            mapping_node = nodes.new(type='ShaderNodeMapping')
            mapping_node.location = -200, 0
            links.new(tex_coord_node.outputs['Object'], mapping_node.inputs['Vector'])

        # Create texture based on type
        if props.led_texture_type == 'SOLID':
            emission_node.inputs['Color'].default_value = props.color1

        elif props.led_texture_type == 'CHECKER':
            checker_node = nodes.new(type='ShaderNodeTexChecker')
            checker_node.inputs['Color1'].default_value = props.color1
            checker_node.inputs['Color2'].default_value = props.color2
            checker_node.inputs['Scale'].default_value = props.checker_scale
            checker_node.location = 0, 0
            links.new(mapping_node.outputs['Vector'], checker_node.inputs['Vector'])
            links.new(checker_node.outputs['Color'], emission_node.inputs['Color'])

        elif props.led_texture_type == 'GRADIENT':
            gradient_node = nodes.new(type='ShaderNodeTexGradient')
            gradient_node.gradient_type = 'LINEAR'
            gradient_node.location = -200, 0
            links.new(mapping_node.outputs['Vector'], gradient_node.inputs['Vector'])

            color_ramp_node = nodes.new(type='ShaderNodeValToRGB')
            color_ramp_node.location = 0, 0
            color_ramp_node.color_ramp.elements[0].color = props.color1
            color_ramp_node.color_ramp.elements[1].color = props.color2
            links.new(gradient_node.outputs['Fac'], color_ramp_node.inputs['Fac'])
            links.new(color_ramp_node.outputs['Color'], emission_node.inputs['Color'])

            if props.gradient_axis == 'X':
                mapping_node.inputs['Rotation'].default_value[1] = math.radians(90)
            elif props.gradient_axis == 'Y':
                mapping_node.inputs['Rotation'].default_value[0] = math.radians(90)

        elif props.led_texture_type == 'WAVE_COLOR':
            # Animated wave pattern using wave texture with driver
            wave_node = nodes.new(type='ShaderNodeTexWave')
            wave_node.wave_type = 'BANDS'
            wave_node.bands_direction = 'X' if props.wave_direction == 'X' else 'Y'
            if props.wave_direction == 'RADIAL':
                wave_node.wave_type = 'RINGS'
            wave_node.inputs['Scale'].default_value = props.texture_scale
            wave_node.inputs['Distortion'].default_value = 2.0
            wave_node.inputs['Detail'].default_value = 2.0
            wave_node.location = -200, 0
            links.new(mapping_node.outputs['Vector'], wave_node.inputs['Vector'])

            # Add driver to Phase Offset for animation
            driver = wave_node.inputs['Phase Offset'].driver_add('default_value').driver
            driver.type = 'SCRIPTED'
            driver.expression = f"frame / 24 * {props.texture_anim_speed}"

            color_ramp_node = nodes.new(type='ShaderNodeValToRGB')
            color_ramp_node.location = 0, 0
            color_ramp_node.color_ramp.elements[0].color = props.color1
            color_ramp_node.color_ramp.elements[1].color = props.color2
            links.new(wave_node.outputs['Fac'], color_ramp_node.inputs['Fac'])
            links.new(color_ramp_node.outputs['Color'], emission_node.inputs['Color'])

        elif props.led_texture_type == 'PULSE':
            # Pulsing/breathing effect using math nodes with driver
            value_node = nodes.new(type='ShaderNodeValue')
            value_node.location = -200, 200

            # Add driver for pulsing animation
            driver = value_node.outputs[0].driver_add('default_value').driver
            driver.type = 'SCRIPTED'
            driver.expression = f"(sin(frame / 24 * {props.texture_anim_speed} * 3.14159 * 2) + 1) / 2"

            # Mix between color1 and color2 based on pulse value
            mix_node = nodes.new(type='ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.location = 100, 0
            mix_node.inputs[6].default_value = props.color1  # A color
            mix_node.inputs[7].default_value = props.color2  # B color
            links.new(value_node.outputs[0], mix_node.inputs['Factor'])
            links.new(mix_node.outputs[2], emission_node.inputs['Color'])

        elif props.led_texture_type == 'RAINBOW':
            # Rainbow cycling using HSV with animated hue
            separate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
            separate_xyz.location = -200, 0
            links.new(mapping_node.outputs['Vector'], separate_xyz.inputs['Vector'])

            # Animated hue offset value
            hue_offset = nodes.new(type='ShaderNodeValue')
            hue_offset.location = -200, 200
            driver = hue_offset.outputs[0].driver_add('default_value').driver
            driver.type = 'SCRIPTED'
            driver.expression = f"(frame / 24 * {props.texture_anim_speed}) % 1"

            # Add position-based hue + animated offset
            math_add = nodes.new(type='ShaderNodeMath')
            math_add.operation = 'ADD'
            math_add.location = 0, 100
            links.new(separate_xyz.outputs['X'], math_add.inputs[0])
            links.new(hue_offset.outputs[0], math_add.inputs[1])

            # Scale the position
            math_mult = nodes.new(type='ShaderNodeMath')
            math_mult.operation = 'MULTIPLY'
            math_mult.inputs[1].default_value = props.texture_scale * 0.1
            math_mult.location = 0, 0
            links.new(math_add.outputs[0], math_mult.inputs[0])

            # Fract to wrap hue
            math_fract = nodes.new(type='ShaderNodeMath')
            math_fract.operation = 'FRACT'
            math_fract.location = 150, 0
            links.new(math_mult.outputs[0], math_fract.inputs[0])

            # Combine HSV (Hue from animation, full Saturation, full Value)
            combine_hsv = nodes.new(type='ShaderNodeCombineHSV')
            combine_hsv.location = 300, 0
            combine_hsv.inputs['S'].default_value = 1.0
            combine_hsv.inputs['V'].default_value = 1.0
            links.new(math_fract.outputs[0], combine_hsv.inputs['H'])
            links.new(combine_hsv.outputs['Color'], emission_node.inputs['Color'])

        elif props.led_texture_type == 'SCAN':
            # Scanning line effect
            separate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
            separate_xyz.location = -200, 0
            links.new(mapping_node.outputs['Vector'], separate_xyz.inputs['Vector'])

            # Animated scan position
            scan_pos = nodes.new(type='ShaderNodeValue')
            scan_pos.location = -200, 200
            driver = scan_pos.outputs[0].driver_add('default_value').driver
            driver.type = 'SCRIPTED'
            driver.expression = f"(frame / 24 * {props.texture_anim_speed}) % 2 - 1"

            # Distance from scan line
            math_sub = nodes.new(type='ShaderNodeMath')
            math_sub.operation = 'SUBTRACT'
            math_sub.location = 0, 100
            out_axis = 'X' if props.wave_direction != 'Y' else 'Y'
            links.new(separate_xyz.outputs[out_axis], math_sub.inputs[0])
            links.new(scan_pos.outputs[0], math_sub.inputs[1])

            # Absolute value
            math_abs = nodes.new(type='ShaderNodeMath')
            math_abs.operation = 'ABSOLUTE'
            math_abs.location = 150, 100
            links.new(math_sub.outputs[0], math_abs.inputs[0])

            # Compare to scan width
            math_less = nodes.new(type='ShaderNodeMath')
            math_less.operation = 'LESS_THAN'
            math_less.inputs[1].default_value = props.scan_width
            math_less.location = 300, 100
            links.new(math_abs.outputs[0], math_less.inputs[0])

            # Mix colors based on scan position
            mix_node = nodes.new(type='ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.location = 200, 0
            mix_node.inputs[6].default_value = props.color2  # Background
            mix_node.inputs[7].default_value = props.color1  # Scan line color
            links.new(math_less.outputs[0], mix_node.inputs['Factor'])
            links.new(mix_node.outputs[2], emission_node.inputs['Color'])

        elif props.led_texture_type == 'NOISE':
            # Animated noise pattern
            noise_node = nodes.new(type='ShaderNodeTexNoise')
            noise_node.inputs['Scale'].default_value = props.texture_scale
            noise_node.inputs['Detail'].default_value = 4.0
            noise_node.location = -100, 0
            links.new(mapping_node.outputs['Vector'], noise_node.inputs['Vector'])

            # Animate W dimension for noise evolution
            driver = noise_node.inputs['W'].driver_add('default_value').driver
            driver.type = 'SCRIPTED'
            driver.expression = f"frame / 24 * {props.texture_anim_speed}"
            noise_node.noise_dimensions = '4D'

            color_ramp_node = nodes.new(type='ShaderNodeValToRGB')
            color_ramp_node.location = 100, 0
            color_ramp_node.color_ramp.elements[0].color = props.color1
            color_ramp_node.color_ramp.elements[1].color = props.color2
            links.new(noise_node.outputs['Fac'], color_ramp_node.inputs['Fac'])
            links.new(color_ramp_node.outputs['Color'], emission_node.inputs['Color'])

        elif props.led_texture_type == 'STROBE':
            # Strobe/flash effect
            value_node = nodes.new(type='ShaderNodeValue')
            value_node.location = 200, 0

            # Add driver for strobe (on/off based on frame)
            driver = value_node.outputs[0].driver_add('default_value').driver
            driver.type = 'SCRIPTED'
            driver.expression = f"1 if (int(frame / 24 * {props.texture_anim_speed} * 10) % 2) == 0 else 0"

            mix_node = nodes.new(type='ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.location = 400, 0
            mix_node.inputs[6].default_value = (0, 0, 0, 1)  # Off state (black)
            mix_node.inputs[7].default_value = props.color1  # On state
            links.new(value_node.outputs[0], mix_node.inputs['Factor'])
            links.new(mix_node.outputs[2], emission_node.inputs['Color'])

        elif props.led_texture_type == 'IMAGE':
            # Image texture (UV checker, custom image, etc.)
            image_node = nodes.new(type='ShaderNodeTexImage')
            image_node.location = 200, 0
            image_loaded = False

            # First check for generated UV checker
            if "UV_Checker_Generated" in bpy.data.images:
                image_node.image = bpy.data.images["UV_Checker_Generated"]
                image_loaded = True
            # Then try to load from path
            elif props.texture_image_path:
                import os
                abs_path = bpy.path.abspath(props.texture_image_path)
                if os.path.exists(abs_path):
                    # Check if image already loaded
                    img_name = os.path.basename(abs_path)
                    if img_name in bpy.data.images:
                        image_node.image = bpy.data.images[img_name]
                    else:
                        image_node.image = bpy.data.images.load(abs_path)
                    image_loaded = True

            if not image_loaded:
                # Create a default UV checker pattern procedurally
                checker_node = nodes.new(type='ShaderNodeTexChecker')
                checker_node.inputs['Scale'].default_value = 8.0
                checker_node.inputs['Color1'].default_value = (1.0, 0.0, 1.0, 1.0)  # Magenta
                checker_node.inputs['Color2'].default_value = (0.0, 0.0, 0.0, 1.0)  # Black
                checker_node.location = 200, 0
                links.new(mapping_node.outputs['Vector'], checker_node.inputs['Vector'])
                links.new(checker_node.outputs['Color'], emission_node.inputs['Color'])
                return mat

            links.new(mapping_node.outputs['Vector'], image_node.inputs['Vector'])
            links.new(image_node.outputs['Color'], emission_node.inputs['Color'])

        return mat

    def execute(self, context):
        props = context.scene.kinetic_led
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            self.report({'ERROR'}, "No LED mesh objects selected to apply texture.")
            return {'CANCELLED'}

        # Calculate grid bounds from selected objects
        min_x = min([obj.location.x for obj in selected_objects])
        max_x = max([obj.location.x for obj in selected_objects])
        min_y = min([obj.location.y for obj in selected_objects])
        max_y = max([obj.location.y for obj in selected_objects])

        # Avoid division by zero if grid is a single line or point
        if min_x == max_x:
            max_x = min_x + 1.0
        if min_y == max_y:
            max_y = min_y + 1.0

        # Update stored bounds
        props.grid_bounds_min_x = min_x
        props.grid_bounds_max_x = max_x
        props.grid_bounds_min_y = min_y
        props.grid_bounds_max_y = max_y
        props.total_panels_created = len(selected_objects)

        # Create material with pattern name, passing calculated bounds
        mat_name = f"LED_{props.led_texture_type}_Material"
        mat = self.create_animated_material(context, props, mat_name, min_x, max_x, min_y, max_y)

        # Apply material to all selected LED objects
        for obj in selected_objects:
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

        grid_w = max_x - min_x
        grid_h = max_y - min_y
        self.report({'INFO'}, f"Applied {props.led_texture_type} texture to {len(selected_objects)} LEDs | Bounds: {grid_w:.2f} x {grid_h:.2f} m")
        return {'FINISHED'}

# ----------------------------------------------------
# RECALCULATE BOUNDS FROM SELECTION
# ----------------------------------------------------
class KINETIC_OT_recalculate_bounds(bpy.types.Operator):
    bl_idname = "kinetic.recalculate_bounds"
    bl_label = "Recalculate Bounds"
    bl_description = "Recalculate grid bounds from selected objects for unified texture mapping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        selected = context.selected_objects

        if not selected:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        xs = [obj.location.x for obj in selected]
        ys = [obj.location.y for obj in selected]

        props.grid_bounds_min_x = min(xs)
        props.grid_bounds_max_x = max(xs)
        props.grid_bounds_min_y = min(ys)
        props.grid_bounds_max_y = max(ys)
        props.total_panels_created = len(selected)

        grid_w = props.grid_bounds_max_x - props.grid_bounds_min_x
        grid_h = props.grid_bounds_max_y - props.grid_bounds_min_y

        self.report({'INFO'}, f"Bounds recalculated: {grid_w:.2f} x {grid_h:.2f} m from {len(selected)} objects")
        return {'FINISHED'}


# ----------------------------------------------------
# GENERATE UV CHECKER TEXTURE
# ----------------------------------------------------
class KINETIC_OT_download_uv_checker(bpy.types.Operator):
    bl_idname = "kinetic.download_uv_checker"
    bl_label = "Generate UV Checker"
    bl_description = "Generate a UV checker texture for testing UV mapping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led

        # Create a UV checker image procedurally
        img_name = "UV_Checker_Generated"
        size = 1024  # 1K resolution

        # Check if image already exists
        if img_name in bpy.data.images:
            img = bpy.data.images[img_name]
            bpy.data.images.remove(img)

        # Create new image
        img = bpy.data.images.new(img_name, width=size, height=size)

        # Generate UV checker pattern
        pixels = []
        grid_size = 8  # 8x8 checker grid
        cell_size = size // grid_size

        # Colors for the UV checker pattern
        colors = [
            (1.0, 0.0, 0.0, 1.0),    # Red
            (0.0, 1.0, 0.0, 1.0),    # Green
            (0.0, 0.0, 1.0, 1.0),    # Blue
            (1.0, 1.0, 0.0, 1.0),    # Yellow
            (1.0, 0.0, 1.0, 1.0),    # Magenta
            (0.0, 1.0, 1.0, 1.0),    # Cyan
            (1.0, 0.5, 0.0, 1.0),    # Orange
            (0.5, 0.0, 1.0, 1.0),    # Purple
        ]

        for y in range(size):
            for x in range(size):
                cell_x = x // cell_size
                cell_y = y // cell_size

                # Checker pattern with different colors per row
                if (cell_x + cell_y) % 2 == 0:
                    color = colors[cell_y % len(colors)]
                else:
                    # Darker shade of the color
                    base_color = colors[cell_y % len(colors)]
                    color = (base_color[0] * 0.3, base_color[1] * 0.3, base_color[2] * 0.3, 1.0)

                # Add grid lines
                local_x = x % cell_size
                local_y = y % cell_size
                if local_x < 2 or local_y < 2 or local_x >= cell_size - 2 or local_y >= cell_size - 2:
                    color = (0.2, 0.2, 0.2, 1.0)  # Dark gray grid lines

                # Add coordinate labels in center of each cell
                center_x = cell_size // 2
                center_y = cell_size // 2
                if abs(local_x - center_x) < 15 and abs(local_y - center_y) < 15:
                    color = (1.0, 1.0, 1.0, 1.0)  # White center marker

                pixels.extend(color)

        img.pixels = pixels
        img.pack()

        # Save path reference
        props.texture_image_path = f"//UV_Checker_Generated"

        self.report({'INFO'}, f"Generated UV Checker texture: {img_name} ({size}x{size})")
        return {'FINISHED'}


# ----------------------------------------------------
# CLEAR ANIMATION
# ----------------------------------------------------
class KINETIC_OT_clear_animation(bpy.types.Operator):
    bl_idname = "kinetic.clear_animation"
    bl_label = "Clear Animation"
    bl_description = "Remove animation from selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            clear_object_animation(obj)
            # Reset Z location to 0
            obj.location.z = 0
            count += 1
        self.report({'INFO'}, f"Cleared animation from {count} objects")
        return {'FINISHED'}

# ----------------------------------------------------
# CLEAR ALL (REMOVE ADDON OBJECTS)
# ----------------------------------------------------
class KINETIC_OT_clear_all(bpy.types.Operator):
    bl_idname = "kinetic.clear_all"
    bl_label = "Clear All"
    bl_description = "Remove LED grid, strips, cables, winches and all related objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed_count = 0

        # Find and remove LED_GRID and LED_STRIP collections
        collections_to_remove = []
        for coll in bpy.data.collections:
            if coll.name.startswith("LED_GRID") or coll.name.startswith("LED_STRIP"):
                collections_to_remove.append(coll)

        for coll in collections_to_remove:
            # Remove all objects in the collection
            for obj in list(coll.objects):
                # Clear constraints first
                obj.constraints.clear()
                # Clear animation
                clear_object_animation(obj)
                bpy.data.objects.remove(obj, do_unlink=True)
                removed_count += 1
            # Remove the collection
            bpy.data.collections.remove(coll)

        # Remove any remaining cables, anchors, and winches
        objects_to_remove = []
        for obj in bpy.data.objects:
            if obj.name.startswith("WINCH_") and "winch_index" in obj: # Only remove actual winches
                objects_to_remove.append(obj)

        for obj in objects_to_remove:
            clear_object_animation(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
            removed_count += 1

        # Clear animation from any remaining selected objects
        for obj in context.selected_objects:
            clear_object_animation(obj)
            obj.constraints.clear()
            obj.location.z = 0

        self.report({'INFO'}, f"Removed {removed_count} objects")
        return {'FINISHED'}

# ----------------------------------------------------
# UI PANELS (Collapsible Sub-panels)
# ----------------------------------------------------

# Main Panel
class KINETIC_PT_main(bpy.types.Panel):
    bl_label = "Kinetic LED Ceiling"
    bl_idname = "KINETIC_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        layout.prop(props, "system_mode", expand=True)

# Grid Settings Sub-panel
class KINETIC_PT_grid(bpy.types.Panel):
    bl_label = "Grid Settings"
    bl_idname = "KINETIC_PT_grid"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='MESH_GRID')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "grid_count_x")
        col.prop(props, "grid_count_y")
        col.prop(props, "grid_spacing")
        layout.operator("kinetic.create_grid")

# Strip Setup Sub-panel
class KINETIC_PT_strip(bpy.types.Panel):
    bl_label = "Strip Setup (Winch Control)"
    bl_idname = "KINETIC_PT_strip"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'WINCH'

    def draw_header(self, context):
        self.layout.label(text="", icon='IPO_BEZIER')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led

        col = layout.column(align=True)
        col.prop(props, "strip_display_count")
        col.prop(props, "strip_display_size")
        col.prop(props, "strip_gap")
        col.prop(props, "strip_axis")
        col.prop(props, "strip_winch_mode")

        layout.separator()
        layout.operator("kinetic.create_strip", icon='ADD')

        # Duplication settings
        box = layout.box()
        box.label(text="Duplicate Strip", icon='MOD_ARRAY')
        col = box.column(align=True)
        col.prop(props, "strip_duplicate_count")
        col.prop(props, "strip_duplicate_axis")
        col.prop(props, "strip_duplicate_spacing")
        box.operator("kinetic.duplicate_strip", icon='DUPLICATE')

        layout.separator()


# Animation Settings Sub-panel
class KINETIC_PT_anim_settings(bpy.types.Panel):
    bl_label = "Animation Settings"
    bl_idname = "KINETIC_PT_anim_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"

    def draw_header(self, context):
        self.layout.label(text="", icon='DRIVER')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "anim_z_offset")
        layout.operator("kinetic.clear_animation", icon='X')

# Wave Sub-panel
class KINETIC_PT_wave(bpy.types.Panel):
    bl_label = "Wave"
    bl_idname = "KINETIC_PT_wave"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='MOD_WAVE')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "wave_amplitude")
        col.prop(props, "wave_speed")
        layout.operator("kinetic.wave_animation")

# Radial Sub-panel
class KINETIC_PT_radial(bpy.types.Panel):
    bl_label = "Radial"
    bl_idname = "KINETIC_PT_radial"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='FORCE_VORTEX')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "radial_amplitude")
        col.prop(props, "radial_speed")
        layout.operator("kinetic.radial_animation")

# Ramp Sub-panel
class KINETIC_PT_ramp(bpy.types.Panel):
    bl_label = "Ramp"
    bl_idname = "KINETIC_PT_ramp"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='SORT_ASC')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "ramp_amplitude")
        col.prop(props, "ramp_speed")
        col.prop(props, "ramp_direction")
        layout.operator("kinetic.ramp_animation")

# Circular Sub-panel
class KINETIC_PT_circular(bpy.types.Panel):
    bl_label = "Circular"
    bl_idname = "KINETIC_PT_circular"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='MESH_CIRCLE')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "circular_amplitude")
        col.prop(props, "circular_speed")
        col.prop(props, "circular_rings")
        layout.operator("kinetic.circular_animation")

# Chess Sub-panel
class KINETIC_PT_chess(bpy.types.Panel):
    bl_label = "Chess"
    bl_idname = "KINETIC_PT_chess"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='VIEW_ORTHO')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "chess_amplitude")
        col.prop(props, "chess_speed")
        col.prop(props, "chess_cell_size")
        layout.operator("kinetic.chess_animation")

# Text Sub-panel
class KINETIC_PT_text(bpy.types.Panel):
    bl_label = "Text"
    bl_idname = "KINETIC_PT_text"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='FONT_DATA')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "text_content")
        col.prop(props, "text_amplitude")
        col.prop(props, "text_speed")
        col.prop(props, "text_scroll")
        layout.operator("kinetic.text_animation")

# Random Sub-panel
class KINETIC_PT_random(bpy.types.Panel):
    bl_label = "Random"
    bl_idname = "KINETIC_PT_random"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'GRID'

    def draw_header(self, context):
        self.layout.label(text="", icon='PARTICLE_DATA')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "random_amplitude")
        col.prop(props, "random_speed")
        col.prop(props, "random_seed")
        layout.operator("kinetic.random_animation")

# Winch Animation Patterns Panel
class KINETIC_PT_winch_patterns(bpy.types.Panel):
    bl_label = "Winch Animation Patterns"
    bl_idname = "KINETIC_PT_winch_patterns"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.kinetic_led.system_mode == 'WINCH'

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led

        # Wave
        box = layout.box()
        box.label(text="Wave", icon='MOD_WAVE')
        col = box.column(align=True)
        col.prop(props, "wave_amplitude")
        col.prop(props, "wave_speed")
        box.operator("kinetic.winch_wave")

        # Radial
        box = layout.box()
        box.label(text="Radial", icon='FORCE_VORTEX')
        col = box.column(align=True)
        col.prop(props, "radial_amplitude")
        col.prop(props, "radial_speed")
        box.operator("kinetic.winch_radial")

        # Ramp
        box = layout.box()
        box.label(text="Ramp", icon='SORT_ASC')
        col = box.column(align=True)
        col.prop(props, "ramp_amplitude")
        col.prop(props, "ramp_speed")
        col.prop(props, "ramp_direction")
        box.operator("kinetic.winch_ramp")

        # Circular
        box = layout.box()
        box.label(text="Circular", icon='MESH_CIRCLE')
        col = box.column(align=True)
        col.prop(props, "circular_amplitude")
        col.prop(props, "circular_speed")
        col.prop(props, "circular_rings")
        box.operator("kinetic.winch_circular")

        # Random
        box = layout.box()
        box.label(text="Random", icon='PARTICLE_DATA')
        col = box.column(align=True)
        col.prop(props, "random_amplitude")
        col.prop(props, "random_speed")
        col.prop(props, "random_seed")
        box.operator("kinetic.winch_random")

# LED Textures Sub-panel
class KINETIC_PT_led_textures(bpy.types.Panel):
    bl_label = "LED Textures"
    bl_idname = "KINETIC_PT_led_textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon='MATERIAL')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led

        # Statistics box
        box = layout.box()
        box.label(text="Current Setup:", icon='INFO')
        if props.total_strips_created > 0:
            box.label(text=f"Strips: {props.total_strips_created}")
        box.label(text=f"Panels: {props.total_panels_created}")
        grid_w = props.grid_bounds_max_x - props.grid_bounds_min_x
        grid_h = props.grid_bounds_max_y - props.grid_bounds_min_y
        box.label(text=f"Bounds: {grid_w:.2f} x {grid_h:.2f} m")
        box.operator("kinetic.recalculate_bounds", icon='FILE_REFRESH', text="Recalculate from Selection")

        layout.separator()
        layout.prop(props, "led_texture_type")

        # Unified mapping toggle
        layout.prop(props, "unified_texture_mapping")

        # Image texture settings
        if props.led_texture_type == 'IMAGE':
            box = layout.box()
            box.label(text="Image Texture:", icon='IMAGE_DATA')
            box.prop(props, "texture_image_path", text="")
            box.operator("kinetic.download_uv_checker", icon='URL', text="Generate UV Checker")

        # Color settings
        if props.led_texture_type != 'IMAGE':
            box = layout.box()
            box.label(text="Colors:", icon='COLOR')
            col = box.column(align=True)
            col.prop(props, "color1")
            if props.led_texture_type not in ['SOLID', 'RAINBOW', 'STROBE']:
                col.prop(props, "color2")

        # Pattern-specific settings
        if props.led_texture_type == 'CHECKER':
            layout.prop(props, "checker_scale")
        elif props.led_texture_type == 'GRADIENT':
            layout.prop(props, "gradient_axis")
        elif props.led_texture_type in ['WAVE_COLOR', 'SCAN']:
            box = layout.box()
            box.label(text="Wave Settings:", icon='MOD_WAVE')
            box.prop(props, "wave_direction")
            if props.led_texture_type == 'SCAN':
                box.prop(props, "scan_width")

        # Animation settings for animated patterns
        if props.led_texture_type in ['WAVE_COLOR', 'PULSE', 'RAINBOW', 'SCAN', 'NOISE', 'STROBE']:
            box = layout.box()
            box.label(text="Animation:", icon='ANIM')
            col = box.column(align=True)
            col.prop(props, "texture_anim_speed")
            if props.led_texture_type in ['WAVE_COLOR', 'RAINBOW', 'NOISE']:
                col.prop(props, "texture_scale")

        # Emission settings
        layout.prop(props, "emission_strength")

        # Apply button
        layout.separator()
        layout.operator("kinetic.apply_led_texture", icon='TEXTURE', text="Apply Texture to Selection")

# Cleanup Sub-panel
class KINETIC_PT_cleanup(bpy.types.Panel):
    bl_label = "Cleanup"
    bl_idname = "KINETIC_PT_cleanup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kinetic LED'
    bl_parent_id = "KINETIC_PT_main"

    def draw_header(self, context):
        self.layout.label(text="", icon='TRASH')

    def draw(self, context):
        layout = self.layout
        layout.operator("kinetic.clear_all", icon='CANCEL')

# ----------------------------------------------------
# REGISTER
# ----------------------------------------------------
classes = [
    KineticLEDProperties,
    KINETIC_OT_create_grid,
    KINETIC_OT_create_strip,
    KINETIC_OT_duplicate_strip,
    # Winch animation operators
    KINETIC_OT_winch_wave,
    KINETIC_OT_winch_radial,
    KINETIC_OT_winch_ramp,
    KINETIC_OT_winch_circular,
    KINETIC_OT_winch_random,
    # Grid animation operators
    KINETIC_OT_wave_animation,
    KINETIC_OT_radial_animation,
    KINETIC_OT_ramp_animation,
    KINETIC_OT_circular_animation,
    KINETIC_OT_chess_animation,
    KINETIC_OT_text_animation,
    KINETIC_OT_random_animation,
    KINETIC_OT_apply_led_texture,
    KINETIC_OT_recalculate_bounds,
    KINETIC_OT_download_uv_checker,
    KINETIC_OT_clear_animation,
    KINETIC_OT_clear_all,
    # UI Panels (order matters - parent first, then children)
    KINETIC_PT_main,
    KINETIC_PT_grid,
    KINETIC_PT_strip,
    KINETIC_PT_anim_settings,
    KINETIC_PT_wave,
    KINETIC_PT_radial,
    KINETIC_PT_ramp,
    KINETIC_PT_circular,
    KINETIC_PT_chess,
    KINETIC_PT_text,
    KINETIC_PT_random,
    KINETIC_PT_winch_patterns,
    KINETIC_PT_led_textures,
    KINETIC_PT_cleanup,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kinetic_led = bpy.props.PointerProperty(type=KineticLEDProperties)

def unregister():
    del bpy.types.Scene.kinetic_led
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()