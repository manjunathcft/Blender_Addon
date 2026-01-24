bl_info = {
    "name": "Kinetic LED Ceiling System",
    "author": "manManjunath",
    "version": (2, 4, 0),
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

    # Loop frames settings
    use_loop_frames: bpy.props.BoolProperty(
        name="Use Loop Frames",
        default=False,
        description="Set exact number of frames for one complete animation cycle"
    )
    loop_frames: bpy.props.IntProperty(
        name="Loop Frames",
        default=120,
        min=1,
        max=10000,
        description="Number of frames for one complete animation loop"
    )

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
    chess_move_distance: bpy.props.FloatProperty(
        name="Move Distance",
        default=0.5,
        min=0.01,
        max=10,
        unit='LENGTH',
        description="Distance panels move DOWN"
    )
    chess_speed: bpy.props.FloatProperty(
        name="Speed",
        default=1.0,
        min=0.1,
        max=500,
        description="Animation speed"
    )
    chess_cell_size: bpy.props.IntProperty(
        name="Cell Size",
        default=1,
        min=1,
        max=10,
        description="Size of chess cells in grid units"
    )


# ----------------------------------------------------
# UTILITY FUNCTIONS
# ----------------------------------------------------
def get_anim_speed(props, default_speed):
    """Get animation speed - either from loop_frames or default speed property"""
    if props.use_loop_frames:
        # For sin(frame/speed) to complete one cycle: frames/speed = 2*pi
        # So speed = frames / (2*pi)
        return props.loop_frames / (2 * math.pi)
    return default_speed


def clear_object_animation(obj):
    """Remove all animation data and drivers from an object's Z location"""
    obj.driver_remove("location", 2)
    if obj.animation_data:
        obj.animation_data_clear()


def get_strip_winches():
    winches = [obj for obj in bpy.data.objects if "winch_index" in obj]
    strip_winches = {}
    if not winches:
        return strip_winches, 0

    for winch in winches:
        parts = winch.name.split("_")
        strip_key = "0"
        winch_idx = -1
        if len(parts) == 2:
            strip_key = "0"
            winch_idx = int(parts[1])
        elif len(parts) == 3:
            strip_key = parts[1]
            winch_idx = int(parts[2])

        if strip_key not in strip_winches:
            strip_winches[strip_key] = []
        strip_winches[strip_key].append((winch_idx, winch))

    sorted_strip_keys = sorted(strip_winches.keys(), key=int)
    sorted_strip_winches = {}
    for key in sorted_strip_keys:
        winch_list = strip_winches[key]
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
    bl_description = "Create grid from selected panel - preserves panel height/position"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        panel = context.active_object
        if not panel:
            self.report({'ERROR'}, "Select one LED panel object")
            return {'CANCELLED'}

        # Get source panel position
        source_x = panel.location.x
        source_y = panel.location.y
        source_z = panel.location.z  # Preserve height

        grid_coll = bpy.data.collections.new("LED_GRID")
        context.scene.collection.children.link(grid_coll)

        panel_count = 0
        for x in range(props.grid_count_x):
            for y in range(props.grid_count_y):
                inst = panel.copy()
                inst.data = panel.data
                inst.location = (
                    source_x + x * props.grid_spacing,
                    source_y + y * props.grid_spacing,
                    source_z  # Use source panel height
                )
                # Store original Z for animation reference
                inst["base_z"] = source_z
                grid_coll.objects.link(inst)
                panel_count += 1

        self.report({'INFO'}, f"Created LED Grid: {props.grid_count_x}x{props.grid_count_y} = {panel_count} panels at Z={source_z:.2f}m")
        return {'FINISHED'}

# ----------------------------------------------------
# CREATE LED STRIP WITH WINCHES
# ----------------------------------------------------
class KINETIC_OT_create_strip(bpy.types.Operator):
    bl_idname = "kinetic.create_strip"
    bl_label = "Create LED Strip"
    bl_description = "Create LED strip from selected panel - preserves panel height/position"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        panel = context.active_object
        if not panel:
            self.report({'ERROR'}, "Select one LED panel object")
            return {'CANCELLED'}

        # Get source panel position
        source_x = panel.location.x
        source_y = panel.location.y
        source_z = panel.location.z  # Preserve height

        strip_coll = bpy.data.collections.new("LED_STRIP")
        context.scene.collection.children.link(strip_coll)

        display_size = props.strip_display_size
        gap = props.strip_gap
        total_spacing = display_size + gap
        count = props.strip_display_count
        total_length = (count - 1) * total_spacing

        is_x_axis = props.strip_axis == 'X'

        winch_positions = []
        if props.strip_winch_mode == '3_POINT':
            winch_positions = [0, total_length / 2, total_length]
        else:
            winch_positions = [0, total_length / 4, total_length / 2,
                              3 * total_length / 4, total_length]

        winches = []
        for i, pos in enumerate(winch_positions):
            winch = bpy.data.objects.new(f"WINCH_{i}", None)
            winch.empty_display_type = 'SPHERE'
            winch.empty_display_size = 0.1
            if is_x_axis:
                winch.location = (source_x + pos, source_y, source_z)
            else:
                winch.location = (source_x, source_y + pos, source_z)
            winch["strip_collection"] = strip_coll.name
            winch["winch_index"] = i
            winch["winch_position"] = pos
            winch["total_length"] = total_length
            winch["base_z"] = source_z
            strip_coll.objects.link(winch)
            winches.append(winch)

        panels = []
        for i in range(count):
            inst = panel.copy()
            inst.data = panel.data
            pos = i * total_spacing

            if is_x_axis:
                inst.location = (source_x + pos, source_y, source_z)
            else:
                inst.location = (source_x, source_y + pos, source_z)

            inst["is_strip_panel"] = True
            inst["panel_position"] = pos
            inst["total_length"] = total_length
            inst["strip_collection"] = strip_coll.name
            inst["base_z"] = source_z

            norm_pos = pos / total_length if total_length > 0 else 0
            influence_data = []
            for j, winch_pos in enumerate(winch_positions):
                winch_norm = winch_pos / total_length if total_length > 0 else 0
                distance = abs(norm_pos - winch_norm)
                max_dist = 1.0 / (len(winch_positions) - 1) if len(winch_positions) > 1 else 1.0
                if distance <= max_dist:
                    influence = 1.0 - (distance / max_dist)
                    influence_data.append((j, influence))

            inst["winch_influences"] = str(influence_data)
            strip_coll.objects.link(inst)
            panels.append(inst)

        self.report({'INFO'}, f"Created strip with {count} displays and {len(winches)} winches at Z={source_z:.2f}m")
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

        strip_colls = [c for c in bpy.data.collections if c.name.startswith("LED_STRIP")]
        if not strip_colls:
            self.report({'ERROR'}, "No LED strip found. Create a strip first.")
            return {'CANCELLED'}

        source_coll = strip_colls[0]
        is_strip_x = props.strip_axis == 'X'
        is_dup_x = props.strip_duplicate_axis == 'X'

        all_objects = list(source_coll.objects)
        if not all_objects:
            self.report({'ERROR'}, "Strip collection is empty.")
            return {'CANCELLED'}

        xs = [obj.location.x for obj in all_objects]
        ys = [obj.location.y for obj in all_objects]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        strip_width_x = max_x - min_x
        strip_width_y = max_y - min_y

        total_duplicated = 0

        for dup_idx in range(1, props.strip_duplicate_count + 1):
            if is_dup_x:
                offset_x = dup_idx * (strip_width_x + props.strip_duplicate_spacing) if is_strip_x else dup_idx * props.strip_duplicate_spacing
                offset_y = 0 if is_strip_x else dup_idx * props.strip_duplicate_spacing
            else:
                offset_x = 0 if is_strip_x else dup_idx * props.strip_duplicate_spacing
                offset_y = dup_idx * (strip_width_y + props.strip_duplicate_spacing) if not is_strip_x else dup_idx * props.strip_duplicate_spacing

            new_coll = bpy.data.collections.new(f"LED_STRIP_{dup_idx}")
            context.scene.collection.children.link(new_coll)

            winch_mapping = {}

            for obj in source_coll.objects:
                if obj.name.startswith("WINCH_"):
                    new_obj = obj.copy()
                    new_obj.location = (
                        obj.location.x + offset_x,
                        obj.location.y + offset_y,
                        obj.location.z
                    )
                    old_idx = obj.name.split("_")[1]
                    new_obj.name = f"WINCH_{dup_idx}_{old_idx}"
                    new_obj["strip_collection"] = new_coll.name
                    new_coll.objects.link(new_obj)
                    winch_mapping[obj.name] = new_obj.name
                    total_duplicated += 1

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

                    influences_str = obj.get("winch_influences", "[]")
                    try:
                        influences = eval(influences_str)
                        new_obj["winch_influences"] = str(influences)
                        new_obj["winch_prefix"] = f"{dup_idx}"
                    except:
                        pass

                    new_coll.objects.link(new_obj)
                    total_duplicated += 1

        self.report({'INFO'}, f"Created {props.strip_duplicate_count} duplicate strips with {total_duplicated} objects")
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
        speed = get_anim_speed(props, props.wave_speed)
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
                    f"sin(frame/{speed} + {phase}) * {props.wave_amplitude}"
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
        speed = get_anim_speed(props, props.radial_speed)
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found.")
            return {'CANCELLED'}

        clear_winch_animation()

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
                    f"sin(frame/{speed} + {dist}) * {props.radial_amplitude}"
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
        speed = get_anim_speed(props, props.ramp_speed)
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
                else:
                    pos_val = winch.location.x + winch.location.y + strip_idx * 0.5

                drv.expression = (
                    f"{props.anim_z_offset} + "
                    f"((sin(frame/{speed} + {pos_val}*0.5) + 1) / 2) * {props.ramp_amplitude}"
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
    bl_description = "Circular animation pattern from center of winch strips"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        speed = get_anim_speed(props, props.circular_speed)
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found.")
            return {'CANCELLED'}

        # Capture base_z and positions BEFORE clearing
        winch_data = {}
        all_positions = []
        for strip_key, winch_list in strip_winches.items():
            for winch_idx, winch in winch_list:
                if "base_z" not in winch:
                    winch["base_z"] = winch.location.z
                winch_data[winch.name] = {
                    'base_z': winch["base_z"],
                    'x': winch.location.x,
                    'y': winch.location.y
                }
                all_positions.append((winch.location.x, winch.location.y))

        # Calculate center
        if all_positions:
            center_x = sum(p[0] for p in all_positions) / len(all_positions)
            center_y = sum(p[1] for p in all_positions) / len(all_positions)
        else:
            center_x, center_y = 0, 0

        clear_winch_animation()

        # Restore Z positions
        for strip_key, winch_list in strip_winches.items():
            for winch_idx, winch in winch_list:
                winch.location.z = winch_data[winch.name]['base_z']

        for strip_idx, (strip_key, winch_list) in enumerate(strip_winches.items()):
            for i, (winch_idx, winch) in enumerate(winch_list):
                data = winch_data[winch.name]
                base_z = data['base_z']
                rel_x = data['x'] - center_x
                rel_y = data['y'] - center_y
                angle = math.atan2(rel_y, rel_x)

                drv = winch.driver_add("location", 2).driver
                drv.expression = (
                    f"{base_z} + "
                    f"sin(frame/{speed} + {angle} * {props.circular_rings}) * {props.circular_amplitude}"
                )

        panel_count = animate_panels_from_winches()
        self.report({'INFO'}, f"Animated {total_winches} winches from center ({center_x:.2f}, {center_y:.2f})")
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
        speed = get_anim_speed(props, props.wave_speed)
        for obj in context.selected_objects:
            clear_object_animation(obj)
            drv = obj.driver_add("location", 2).driver
            drv.expression = (
                f"{props.anim_z_offset} + sin(frame/{speed} + "
                f"({obj.location.x} + {obj.location.y})*2) * {props.wave_amplitude}"
            )
        return {'FINISHED'}

# ----------------------------------------------------
# RADIAL ANIMATION
# ----------------------------------------------------
class KINETIC_OT_radial_animation(bpy.types.Operator):
    bl_idname = "kinetic.radial_animation"
    bl_label = "Apply Radial Animation"
    bl_description = "Radial wave animation expanding from center of selected panels"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        speed = get_anim_speed(props, props.radial_speed)
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Calculate center of all selected panels
        center_x = sum(obj.location.x for obj in selected) / len(selected)
        center_y = sum(obj.location.y for obj in selected) / len(selected)

        for obj in selected:
            # Capture base_z before clearing
            if "base_z" not in obj:
                obj["base_z"] = obj.location.z
            base_z = obj["base_z"]

            clear_object_animation(obj)
            obj.location.z = base_z

            # Calculate distance from center (pre-calculate since sqrt not available in drivers)
            rel_x = obj.location.x - center_x
            rel_y = obj.location.y - center_y
            dist = math.sqrt(rel_x**2 + rel_y**2)

            drv = obj.driver_add("location", 2).driver
            drv.expression = (
                f"{base_z} + sin(frame/{speed} + {dist}) * {props.radial_amplitude}"
            )

        self.report({'INFO'}, f"Applied Radial animation to {len(selected)} panels from center ({center_x:.2f}, {center_y:.2f})")
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
        speed = get_anim_speed(props, props.ramp_speed)
        for obj in context.selected_objects:
            clear_object_animation(obj)
            drv = obj.driver_add("location", 2).driver

            if props.ramp_direction == 'X':
                pos_expr = f"{obj.location.x}"
            elif props.ramp_direction == 'Y':
                pos_expr = f"{obj.location.y}"
            else:
                pos_expr = f"({obj.location.x} + {obj.location.y})"

            drv.expression = (
                f"{props.anim_z_offset} + "
                f"((sin(frame/{speed} + {pos_expr}*0.5) + 1) / 2) * {props.ramp_amplitude}"
            )
        return {'FINISHED'}

# ----------------------------------------------------
# CIRCULAR ANIMATION
# ----------------------------------------------------
class KINETIC_OT_circular_animation(bpy.types.Operator):
    bl_idname = "kinetic.circular_animation"
    bl_label = "Apply Circular Animation"
    bl_description = "Circular wave animation from the center of selected panels"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        speed = get_anim_speed(props, props.circular_speed)
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Calculate center of all selected panels
        center_x = sum(obj.location.x for obj in selected) / len(selected)
        center_y = sum(obj.location.y for obj in selected) / len(selected)

        for obj in selected:
            # Capture base_z before clearing
            if "base_z" not in obj:
                obj["base_z"] = obj.location.z
            base_z = obj["base_z"]

            clear_object_animation(obj)
            obj.location.z = base_z

            # Calculate relative position from center
            rel_x = obj.location.x - center_x
            rel_y = obj.location.y - center_y

            drv = obj.driver_add("location", 2).driver
            drv.expression = (
                f"{base_z} + "
                f"sin(frame/{speed} + "
                f"atan2({rel_y}, {rel_x}) * {props.circular_rings}) * {props.circular_amplitude}"
            )

        self.report({'INFO'}, f"Applied Circular animation to {len(selected)} panels from center ({center_x:.2f}, {center_y:.2f})")
        return {'FINISHED'}


# ----------------------------------------------------
# CHESS ANIMATION
# ----------------------------------------------------
class KINETIC_OT_chess_animation(bpy.types.Operator):
    bl_idname = "kinetic.chess_animation"
    bl_label = "Apply Chess Animation"
    bl_description = "Chess pattern - panels move DOWN alternately"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        speed = get_anim_speed(props, props.chess_speed)
        selected = list(context.selected_objects)
        if not selected:
            return {'CANCELLED'}

        # Get grid bounds
        xs = [obj.location.x for obj in selected]
        ys = [obj.location.y for obj in selected]
        min_x, min_y = min(xs), min(ys)
        spacing = props.grid_spacing if props.grid_spacing > 0 else 0.26

        for obj in selected:
            # Capture base_z before clearing
            if "base_z" not in obj:
                obj["base_z"] = obj.location.z
            base_z = obj["base_z"]

            clear_object_animation(obj)
            obj.location.z = base_z

            # Calculate grid position
            grid_x = int(round((obj.location.x - min_x) / spacing))
            grid_y = int(round((obj.location.y - min_y) / spacing))
            # Chess pattern: alternating cells
            cell_x = grid_x // props.chess_cell_size
            cell_y = grid_y // props.chess_cell_size
            is_white = (cell_x + cell_y) % 2

            # Phase offset for alternating pattern (pi for cosine-based alternation)
            phase = 0 if is_white else 3.14159

            drv = obj.driver_add("location", 2).driver
            # Smooth ease-in-out using (1 - cos(x)) / 2 for natural motion
            drv.expression = (
                f"{base_z} - "
                f"((1 - cos(frame/{speed} + {phase})) / 2) * {props.chess_move_distance}"
            )

        self.report({'INFO'}, f"Chess animation applied to {len(selected)} panels")
        return {'FINISHED'}


# ----------------------------------------------------
# WINCH CHESS ANIMATION
# ----------------------------------------------------
class KINETIC_OT_winch_chess(bpy.types.Operator):
    bl_idname = "kinetic.winch_chess"
    bl_label = "Chess Pattern"
    bl_description = "Chess animation pattern for winch strips - alternating strips move DOWN"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kinetic_led
        speed = get_anim_speed(props, props.chess_speed)
        strip_winches, total_winches = get_strip_winches()

        if total_winches == 0:
            self.report({'ERROR'}, "No winches found. Create a strip first.")
            return {'CANCELLED'}

        # Capture base_z BEFORE clearing
        winch_data = {}
        for strip_key, winch_list in strip_winches.items():
            for winch_idx, winch in winch_list:
                if "base_z" not in winch:
                    winch["base_z"] = winch.location.z
                winch_data[winch.name] = winch["base_z"]

        clear_winch_animation()

        # Restore Z positions
        for strip_key, winch_list in strip_winches.items():
            for winch_idx, winch in winch_list:
                winch.location.z = winch_data[winch.name]

        # Apply chess pattern based on strip index (alternating strips)
        for strip_idx, (strip_key, winch_list) in enumerate(strip_winches.items()):
            # Chess pattern: alternating strips (pi for cosine-based alternation)
            cell_idx = strip_idx // props.chess_cell_size
            is_black = cell_idx % 2
            phase = is_black * 3.14159

            for i, (winch_idx, winch) in enumerate(winch_list):
                base_z = winch_data[winch.name]

                drv = winch.driver_add("location", 2).driver
                # Smooth ease-in-out using (1 - cos(x)) / 2 for natural motion
                drv.expression = (
                    f"{base_z} - "
                    f"((1 - cos(frame/{speed} + {phase})) / 2) * {props.chess_move_distance}"
                )

        panel_count = animate_panels_from_winches()
        self.report({'INFO'}, f"Chess animation: {total_winches} winches, {len(strip_winches)} strips")
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

        collections_to_remove = []
        for coll in bpy.data.collections:
            if coll.name.startswith("LED_GRID") or coll.name.startswith("LED_STRIP"):
                collections_to_remove.append(coll)

        for coll in collections_to_remove:
            for obj in list(coll.objects):
                obj.constraints.clear()
                clear_object_animation(obj)
                bpy.data.objects.remove(obj, do_unlink=True)
                removed_count += 1
            bpy.data.collections.remove(coll)

        objects_to_remove = []
        for obj in bpy.data.objects:
            if obj.name.startswith("WINCH_") and "winch_index" in obj:
                objects_to_remove.append(obj)

        for obj in objects_to_remove:
            clear_object_animation(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
            removed_count += 1

        for obj in context.selected_objects:
            clear_object_animation(obj)
            obj.constraints.clear()
            obj.location.z = 0

        self.report({'INFO'}, f"Removed {removed_count} objects")
        return {'FINISHED'}

# ----------------------------------------------------
# UI PANELS
# ----------------------------------------------------

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

        box = layout.box()
        box.label(text="Duplicate Strip", icon='MOD_ARRAY')
        col = box.column(align=True)
        col.prop(props, "strip_duplicate_count")
        col.prop(props, "strip_duplicate_axis")
        col.prop(props, "strip_duplicate_spacing")
        box.operator("kinetic.duplicate_strip", icon='DUPLICATE')

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

        # Loop frames settings
        box = layout.box()
        box.label(text="Loop Settings", icon='FILE_REFRESH')
        row = box.row()
        row.prop(props, "use_loop_frames")
        sub = box.column()
        sub.enabled = props.use_loop_frames
        sub.prop(props, "loop_frames")

        layout.operator("kinetic.clear_animation", icon='X')

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
        self.layout.label(text="", icon='MESH_PLANE')

    def draw(self, context):
        layout = self.layout
        props = context.scene.kinetic_led
        col = layout.column(align=True)
        col.prop(props, "chess_move_distance")
        col.prop(props, "chess_speed")
        col.prop(props, "chess_cell_size")
        layout.operator("kinetic.chess_animation")


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

        box = layout.box()
        box.label(text="Wave", icon='MOD_WAVE')
        col = box.column(align=True)
        col.prop(props, "wave_amplitude")
        col.prop(props, "wave_speed")
        box.operator("kinetic.winch_wave")

        box = layout.box()
        box.label(text="Radial", icon='FORCE_VORTEX')
        col = box.column(align=True)
        col.prop(props, "radial_amplitude")
        col.prop(props, "radial_speed")
        box.operator("kinetic.winch_radial")

        box = layout.box()
        box.label(text="Ramp", icon='SORT_ASC')
        col = box.column(align=True)
        col.prop(props, "ramp_amplitude")
        col.prop(props, "ramp_speed")
        col.prop(props, "ramp_direction")
        box.operator("kinetic.winch_ramp")

        box = layout.box()
        box.label(text="Circular", icon='MESH_CIRCLE')
        col = box.column(align=True)
        col.prop(props, "circular_amplitude")
        col.prop(props, "circular_speed")
        col.prop(props, "circular_rings")
        box.operator("kinetic.winch_circular")

        box = layout.box()
        box.label(text="Chess", icon='MESH_PLANE')
        col = box.column(align=True)
        col.prop(props, "chess_move_distance")
        col.prop(props, "chess_speed")
        col.prop(props, "chess_cell_size")
        box.operator("kinetic.winch_chess")


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
    KINETIC_OT_winch_wave,
    KINETIC_OT_winch_radial,
    KINETIC_OT_winch_ramp,
    KINETIC_OT_winch_circular,
    KINETIC_OT_wave_animation,
    KINETIC_OT_radial_animation,
    KINETIC_OT_ramp_animation,
    KINETIC_OT_circular_animation,
    KINETIC_OT_chess_animation,
    KINETIC_OT_winch_chess,
    KINETIC_OT_clear_animation,
    KINETIC_OT_clear_all,
    KINETIC_PT_main,
    KINETIC_PT_grid,
    KINETIC_PT_strip,
    KINETIC_PT_anim_settings,
    KINETIC_PT_wave,
    KINETIC_PT_radial,
    KINETIC_PT_ramp,
    KINETIC_PT_circular,
    KINETIC_PT_chess,
    KINETIC_PT_winch_patterns,
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
