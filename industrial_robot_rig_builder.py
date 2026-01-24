bl_info = {
    "name": "KUKA Robot Rig Builder",
    "author": "Manjunath",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Robot IK",
    "description": "Creates a proper 6-axis KUKA-style industrial robot rig with FK/IK",
    "category": "Rigging",
}

import bpy
from mathutils import Vector, Matrix, Euler
from math import radians, degrees


# -------------------------------------------------
# KUKA ROBOT JOINT CONFIGURATION
# Each joint has: (axis, min_angle, max_angle, description)
# Axis: 'X', 'Y', or 'Z' - the LOCAL rotation axis
# -------------------------------------------------
KUKA_JOINTS = {
    "A1_Base": {
        "axis": "Z",
        "min": -185,
        "max": 185,
        "locked": True,        # Completely fixed - no movement
        "lock_location": True,
        "lock_scale": True,
        "description": "Base (LOCKED - no movement)"
    },
    "A2_Shoulder": {
        "axis": "Y",           # ONLY Y-axis rotation allowed
        "min": -140,
        "max": 168,
        "locked": False,
        "lock_location": True,  # No translation
        "lock_scale": True,     # No scaling
        "description": "Shoulder (Y-axis rotation ONLY)"
    },
    "A3_Elbow": {
        "axis": "Y",           # ONLY Y-axis rotation
        "min": -120,
        "max": 168,
        "locked": False,
        "lock_location": True,
        "lock_scale": True,
        "description": "Elbow (Y-axis rotation ONLY)"
    },
    "A4_Wrist1": {
        "axis": "X",           # ONLY X-axis rotation (roll)
        "min": -350,
        "max": 350,
        "locked": False,
        "lock_location": True,
        "lock_scale": True,
        "description": "Wrist1 (X-axis rotation ONLY)"
    },
    "A5_Wrist2": {
        "axis": "Y",           # ONLY Y-axis rotation
        "min": -125,
        "max": 125,
        "locked": False,
        "lock_location": True,
        "lock_scale": True,
        "description": "Wrist2 (Y-axis rotation ONLY)"
    },
    "A6_Flange": {
        "axis": "X",           # ONLY X-axis rotation (tool roll)
        "min": -350,
        "max": 350,
        "locked": False,
        "lock_location": True,
        "lock_scale": True,
        "description": "Flange (X-axis rotation ONLY)"
    },
}


# -------------------------------------------------
# PROPERTIES
# -------------------------------------------------
class RobotRigProperties(bpy.types.PropertyGroup):
    # Mesh pickers
    mesh_a1_base: bpy.props.PointerProperty(
        name="A1 Base",
        type=bpy.types.Object,
        description="Base pedestal (fixed)",
        poll=lambda self, obj: obj.type == 'MESH'
    )
    mesh_a2_shoulder: bpy.props.PointerProperty(
        name="A2 Shoulder",
        type=bpy.types.Object,
        description="Shoulder segment",
        poll=lambda self, obj: obj.type == 'MESH'
    )
    mesh_a3_elbow: bpy.props.PointerProperty(
        name="A3 Elbow",
        type=bpy.types.Object,
        description="Elbow/upper arm segment",
        poll=lambda self, obj: obj.type == 'MESH'
    )
    mesh_a4_wrist1: bpy.props.PointerProperty(
        name="A4 Wrist 1",
        type=bpy.types.Object,
        description="First wrist segment (roll)",
        poll=lambda self, obj: obj.type == 'MESH'
    )
    mesh_a5_wrist2: bpy.props.PointerProperty(
        name="A5 Wrist 2",
        type=bpy.types.Object,
        description="Second wrist segment (bend)",
        poll=lambda self, obj: obj.type == 'MESH'
    )
    mesh_a6_flange: bpy.props.PointerProperty(
        name="A6 Flange",
        type=bpy.types.Object,
        description="End flange/tool mount",
        poll=lambda self, obj: obj.type == 'MESH'
    )

    # Control mode
    use_ik: bpy.props.BoolProperty(
        name="Enable IK Control",
        default=False,
        description="Use IK target for control (experimental). FK is recommended for industrial robots"
    )

    # Base lock
    lock_base: bpy.props.BoolProperty(
        name="Lock Base (A1)",
        default=True,
        description="Keep base completely fixed"
    )


# -------------------------------------------------
# BUILD RIG OPERATOR
# -------------------------------------------------
class ROBOT_OT_build_rig(bpy.types.Operator):
    bl_idname = "robot.build_rig"
    bl_label = "Build KUKA Rig"
    bl_description = "Build a KUKA-style robot rig with proper joint constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.robot_rig_props

        # Gather mesh assignments
        mesh_list = [
            ("A1_Base", props.mesh_a1_base),
            ("A2_Shoulder", props.mesh_a2_shoulder),
            ("A3_Elbow", props.mesh_a3_elbow),
            ("A4_Wrist1", props.mesh_a4_wrist1),
            ("A5_Wrist2", props.mesh_a5_wrist2),
            ("A6_Flange", props.mesh_a6_flange),
        ]

        assigned = [(name, mesh) for name, mesh in mesh_list if mesh is not None]

        if len(assigned) < 2:
            self.report({'ERROR'}, "Assign at least 2 meshes")
            return {'CANCELLED'}

        # Ensure object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # Get mesh positions (origins = joint centers)
        joint_data = []
        for bone_name, mesh_obj in assigned:
            pos = mesh_obj.matrix_world.translation.copy()
            rot = mesh_obj.matrix_world.to_euler()
            joint_data.append((bone_name, pos, rot, mesh_obj))

        # Create armature at world origin
        arm_data = bpy.data.armatures.new("KUKA_Armature")
        arm_data.display_type = 'OCTAHEDRAL'
        arm_obj = bpy.data.objects.new("KUKA_Robot", arm_data)

        # Place armature at base position
        base_pos = joint_data[0][1]
        arm_obj.location = base_pos

        context.collection.objects.link(arm_obj)
        context.view_layer.objects.active = arm_obj
        arm_obj.select_set(True)

        # ---------------------------------
        # CREATE BONES IN EDIT MODE
        # ---------------------------------
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = arm_data.edit_bones

        created_bones = []
        prev_bone = None

        for i, (bone_name, world_pos, world_rot, mesh_obj) in enumerate(joint_data):
            bone = edit_bones.new(bone_name)

            # Head at joint position (local to armature)
            local_pos = world_pos - base_pos
            bone.head = local_pos

            # Tail points to next joint or extends
            if i < len(joint_data) - 1:
                next_pos = joint_data[i + 1][1] - base_pos
                bone.tail = next_pos
            else:
                # Last bone - extend along its axis
                if prev_bone:
                    direction = (local_pos - prev_bone.head).normalized()
                    bone.tail = local_pos + direction * 0.15
                else:
                    bone.tail = local_pos + Vector((0, 0, 0.15))

            # Ensure minimum length
            if (bone.tail - bone.head).length < 0.01:
                bone.tail = bone.head + Vector((0, 0.1, 0))

            # Set bone roll to align with mesh rotation
            # This ensures the local axes match the mesh orientation
            bone.roll = 0

            # Parent to previous
            if prev_bone:
                bone.parent = prev_bone
                bone.use_connect = True

            prev_bone = bone
            created_bones.append((bone_name, mesh_obj, bone.name))

        bpy.ops.object.mode_set(mode='OBJECT')

        # ---------------------------------
        # SETUP POSE CONSTRAINTS
        # ---------------------------------
        bpy.ops.object.mode_set(mode='POSE')

        for bone_name, mesh_obj, actual_name in created_bones:
            pose_bone = arm_obj.pose.bones[actual_name]

            # Get KUKA joint config
            joint_config = None
            for key in KUKA_JOINTS:
                if key in bone_name:
                    joint_config = KUKA_JOINTS[key]
                    break

            if not joint_config:
                continue

            axis = joint_config["axis"]
            min_angle = joint_config["min"]
            max_angle = joint_config["max"]
            is_locked = joint_config["locked"] and props.lock_base

            if is_locked:
                # Completely lock this bone
                pose_bone.lock_location = (True, True, True)
                pose_bone.lock_rotation = (True, True, True)
                pose_bone.lock_rotation_w = True
                pose_bone.lock_scale = (True, True, True)

                # Add locked constraint
                lock_con = pose_bone.constraints.new('LIMIT_ROTATION')
                lock_con.name = "LOCKED"
                lock_con.use_limit_x = True
                lock_con.use_limit_y = True
                lock_con.use_limit_z = True
                lock_con.min_x = lock_con.max_x = 0
                lock_con.min_y = lock_con.max_y = 0
                lock_con.min_z = lock_con.max_z = 0
                lock_con.owner_space = 'LOCAL'
            else:
                # Lock location (no translation allowed)
                if joint_config.get("lock_location", False):
                    pose_bone.lock_location = (True, True, True)

                # Lock scale
                if joint_config.get("lock_scale", False):
                    pose_bone.lock_scale = (True, True, True)

                # Lock non-active rotation axes, allow only the specified axis
                if axis == "X":
                    pose_bone.lock_rotation = (False, True, True)
                elif axis == "Y":
                    pose_bone.lock_rotation = (True, False, True)
                elif axis == "Z":
                    pose_bone.lock_rotation = (True, True, False)

                # Add rotation limit constraint for strict control
                limit_con = pose_bone.constraints.new('LIMIT_ROTATION')
                limit_con.name = f"{bone_name}_Limit"
                limit_con.owner_space = 'LOCAL'
                limit_con.use_transform_limit = True  # Apply during transform

                limit_con.use_limit_x = True
                limit_con.use_limit_y = True
                limit_con.use_limit_z = True

                # Set limits based on active axis - lock others to ZERO
                if axis == "X":
                    limit_con.min_x = radians(min_angle)
                    limit_con.max_x = radians(max_angle)
                    limit_con.min_y = limit_con.max_y = 0
                    limit_con.min_z = limit_con.max_z = 0
                elif axis == "Y":
                    limit_con.min_y = radians(min_angle)
                    limit_con.max_y = radians(max_angle)
                    limit_con.min_x = limit_con.max_x = 0
                    limit_con.min_z = limit_con.max_z = 0
                elif axis == "Z":
                    limit_con.min_z = radians(min_angle)
                    limit_con.max_z = radians(max_angle)
                    limit_con.min_x = limit_con.max_x = 0
                    limit_con.min_y = limit_con.max_y = 0

                # Add Location constraint to prevent any translation
                if joint_config.get("lock_location", False):
                    loc_con = pose_bone.constraints.new('LIMIT_LOCATION')
                    loc_con.name = f"{bone_name}_NoMove"
                    loc_con.owner_space = 'LOCAL'
                    loc_con.use_transform_limit = True
                    loc_con.use_min_x = loc_con.use_max_x = True
                    loc_con.use_min_y = loc_con.use_max_y = True
                    loc_con.use_min_z = loc_con.use_max_z = True
                    loc_con.min_x = loc_con.max_x = 0
                    loc_con.min_y = loc_con.max_y = 0
                    loc_con.min_z = loc_con.max_z = 0

        bpy.ops.object.mode_set(mode='OBJECT')

        # ---------------------------------
        # CREATE IK TARGET (optional)
        # ---------------------------------
        if props.use_ik:
            last_pos = joint_data[-1][1]
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=last_pos + Vector((0, 0.2, 0)))
            ik_target = context.object
            ik_target.name = "KUKA_IK_Target"
            ik_target.empty_display_size = 0.1

            # Add IK constraint to last bone
            context.view_layer.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='POSE')

            last_bone_name = created_bones[-1][2]
            pose_bone = arm_obj.pose.bones[last_bone_name]

            ik_con = pose_bone.constraints.new('IK')
            ik_con.name = "KUKA_IK"
            ik_con.target = ik_target
            ik_con.chain_count = len(created_bones) - 1 if props.lock_base else len(created_bones)
            ik_con.use_stretch = False

            bpy.ops.object.mode_set(mode='OBJECT')

        # ---------------------------------
        # PARENT MESHES TO BONES
        # ---------------------------------
        for bone_name, mesh_obj, actual_name in created_bones:
            if mesh_obj is None:
                continue

            # Store current world transform
            world_matrix = mesh_obj.matrix_world.copy()

            # Parent to bone
            mesh_obj.parent = arm_obj
            mesh_obj.parent_type = 'BONE'
            mesh_obj.parent_bone = actual_name

            # Restore world transform
            mesh_obj.matrix_world = world_matrix

        # ---------------------------------
        # DISPLAY SETTINGS
        # ---------------------------------
        arm_obj.data.display_type = 'STICK'
        arm_obj.show_in_front = True

        # Select armature
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        context.view_layer.objects.active = arm_obj

        mode_str = "IK" if props.use_ik else "FK"
        self.report({'INFO'}, f"KUKA rig created with {len(created_bones)} joints ({mode_str} mode)")
        return {'FINISHED'}


# -------------------------------------------------
# CLEAR ASSIGNMENTS
# -------------------------------------------------
class ROBOT_OT_clear_assignments(bpy.types.Operator):
    bl_idname = "robot.clear_assignments"
    bl_label = "Clear All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.robot_rig_props
        props.mesh_a1_base = None
        props.mesh_a2_shoulder = None
        props.mesh_a3_elbow = None
        props.mesh_a4_wrist1 = None
        props.mesh_a5_wrist2 = None
        props.mesh_a6_flange = None
        return {'FINISHED'}


# -------------------------------------------------
# AUTO ASSIGN
# -------------------------------------------------
class ROBOT_OT_auto_assign(bpy.types.Operator):
    bl_idname = "robot.auto_assign"
    bl_label = "Auto-Assign"
    bl_description = "Assign selected meshes by Z-height (lowest = base)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.robot_rig_props
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'WARNING'}, "Select meshes first")
            return {'CANCELLED'}

        # Sort by Z position (lowest first)
        selected.sort(key=lambda o: o.matrix_world.translation.z)

        slots = [
            "mesh_a1_base", "mesh_a2_shoulder", "mesh_a3_elbow",
            "mesh_a4_wrist1", "mesh_a5_wrist2", "mesh_a6_flange"
        ]

        for i, obj in enumerate(selected[:6]):
            setattr(props, slots[i], obj)

        self.report({'INFO'}, f"Assigned {min(len(selected), 6)} meshes by height")
        return {'FINISHED'}


# -------------------------------------------------
# RESET POSE
# -------------------------------------------------
class ROBOT_OT_reset_pose(bpy.types.Operator):
    bl_idname = "robot.reset_pose"
    bl_label = "Reset Pose"
    bl_description = "Reset robot to rest position"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = bpy.data.objects.get("KUKA_Robot")
        if not arm_obj:
            self.report({'WARNING'}, "KUKA_Robot not found")
            return {'CANCELLED'}

        context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.rot_clear()
        bpy.ops.pose.loc_clear()
        bpy.ops.pose.scale_clear()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Reset IK target if exists
        ik_target = bpy.data.objects.get("KUKA_IK_Target")
        if ik_target and arm_obj.data.bones:
            last_bone = arm_obj.data.bones[-1]
            ik_target.location = arm_obj.matrix_world @ last_bone.tail_local

        self.report({'INFO'}, "Pose reset")
        return {'FINISHED'}


# -------------------------------------------------
# DELETE RIG
# -------------------------------------------------
class ROBOT_OT_delete_rig(bpy.types.Operator):
    bl_idname = "robot.delete_rig"
    bl_label = "Delete Rig"
    bl_description = "Remove rig, keep meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = bpy.data.objects.get("KUKA_Robot")
        if arm_obj:
            # Unparent meshes
            for obj in list(bpy.data.objects):
                if obj.parent == arm_obj:
                    mat = obj.matrix_world.copy()
                    obj.parent = None
                    obj.matrix_world = mat
            bpy.data.objects.remove(arm_obj, do_unlink=True)

        ik_target = bpy.data.objects.get("KUKA_IK_Target")
        if ik_target:
            bpy.data.objects.remove(ik_target, do_unlink=True)

        self.report({'INFO'}, "Rig deleted")
        return {'FINISHED'}


# -------------------------------------------------
# UI PANEL
# -------------------------------------------------
class ROBOT_PT_panel(bpy.types.Panel):
    bl_label = "KUKA Robot Rig"
    bl_idname = "ROBOT_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Robot IK"

    def draw(self, context):
        layout = self.layout
        props = context.scene.robot_rig_props

        # --- MESH ASSIGNMENT ---
        box = layout.box()
        box.label(text="Assign Robot Parts", icon='MESH_DATA')

        row = box.row(align=True)
        row.operator("robot.auto_assign", icon='SORTSIZE')
        row.operator("robot.clear_assignments", text="Clear", icon='X')

        col = box.column(align=True)
        col.prop(props, "mesh_a1_base")
        col.prop(props, "mesh_a2_shoulder")
        col.prop(props, "mesh_a3_elbow")
        col.prop(props, "mesh_a4_wrist1")
        col.prop(props, "mesh_a5_wrist2")
        col.prop(props, "mesh_a6_flange")

        # --- JOINT INFO ---
        box = layout.box()
        box.label(text="Joint Constraints (Strict)", icon='LOCKED')

        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="A1 Base: LOCKED (no movement)")
        col.label(text="A2 Shoulder: Y-rotation ONLY")
        col.label(text="A3 Elbow: Y-rotation ONLY")
        col.label(text="A4 Wrist1: X-rotation ONLY")
        col.label(text="A5 Wrist2: Y-rotation ONLY")
        col.label(text="A6 Flange: X-rotation ONLY")
        col.separator()
        col.label(text="All joints: No translation/scale", icon='INFO')

        # --- OPTIONS ---
        box = layout.box()
        box.label(text="Options", icon='PREFERENCES')
        box.prop(props, "lock_base")
        box.prop(props, "use_ik")

        if not props.use_ik:
            box.label(text="FK Mode: Rotate bones in Pose Mode", icon='INFO')

        # --- BUILD ---
        layout.separator()
        row = layout.row()
        row.scale_y = 2.0
        row.operator("robot.build_rig", icon='ARMATURE_DATA')

        # --- UTILITIES ---
        row = layout.row(align=True)
        row.operator("robot.reset_pose", icon='LOOP_BACK')
        row.operator("robot.delete_rig", icon='TRASH')


# -------------------------------------------------
# REGISTER
# -------------------------------------------------
classes = (
    RobotRigProperties,
    ROBOT_OT_build_rig,
    ROBOT_OT_clear_assignments,
    ROBOT_OT_auto_assign,
    ROBOT_OT_reset_pose,
    ROBOT_OT_delete_rig,
    ROBOT_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.robot_rig_props = bpy.props.PointerProperty(type=RobotRigProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.robot_rig_props


if __name__ == "__main__":
    register()
