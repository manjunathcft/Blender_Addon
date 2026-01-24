
bl_info = {
    "name": "Collections to Unity Exporter",
    "author": "ChatGPT",
    "version": (1, 5, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Unity Export",
    "description": "Export collections as FBX or GLB files for Unity",
    "category": "Import-Export",
}

import bpy
import os
import mathutils


class UnityExportSettings(bpy.types.PropertyGroup):
    export_format: bpy.props.EnumProperty(
        name="Format",
        items=[
            ('GLB', "GLB", "Export as GLB (glTF Binary)"),
            ('FBX', "FBX", "Export as FBX"),
        ],
        default='GLB'
    )


def get_collections_from_selected_objects(context):
    collections = set()
    for obj in context.selected_objects:
        for col in obj.users_collection:
            collections.add(col)
    return list(collections)


def get_combined_bounds(objects):
    """Get the combined bounding box of all objects in world space."""
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')

    for obj in objects:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ mathutils.Vector(corner)
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def export_collection(context, col, directory, export_format):
    """Export a single collection to the specified format using duplicates."""
    bpy.ops.object.select_all(action='DESELECT')

    objs = [o for o in col.objects if o.type == 'MESH']
    if not objs:
        return False

    # Get combined bounds from originals
    bounds_min, bounds_max = get_combined_bounds(objs)

    # Calculate offset to move center-bottom to world origin
    center_x = (bounds_min[0] + bounds_max[0]) / 2
    center_y = (bounds_min[1] + bounds_max[1]) / 2
    bottom_z = bounds_min[2]
    offset = mathutils.Vector((-center_x, -center_y, -bottom_z))

    # Create duplicates for export (move as a group, preserving relative positions)
    duplicates = []
    for obj in objs:
        dup = obj.copy()
        dup.data = obj.data.copy()
        context.scene.collection.objects.link(dup)
        dup.parent = None
        # Apply offset in world space to move entire group together
        new_matrix = obj.matrix_world.copy()
        new_matrix.translation += offset
        dup.matrix_world = new_matrix
        duplicates.append(dup)

    context.view_layer.update()

    # Create Empty Group at world origin
    empty = bpy.data.objects.new(f"{col.name}_GRP", None)
    context.scene.collection.objects.link(empty)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.location = (0, 0, 0)

    # Parent duplicates to empty and select them
    bpy.ops.object.select_all(action='DESELECT')
    for dup in duplicates:
        dup.parent = empty
        dup.select_set(True)

    empty.select_set(True)
    context.view_layer.objects.active = empty

    if export_format == 'GLB':
        export_path = os.path.join(directory, f"{col.name}.glb")
        bpy.ops.export_scene.gltf(
            filepath=export_path,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_materials='EXPORT',
            export_normals=True,
            export_texcoords=True,
        )
    else:  # FBX
        export_path = os.path.join(directory, f"{col.name}.fbx")
        bpy.ops.export_scene.fbx(
            filepath=export_path,
            use_selection=True,
            apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z',
            axis_up='Y',
            use_mesh_modifiers=True,
            mesh_smooth_type='FACE',
            add_leaf_bones=False,
            bake_anim=False,
        )

    # Clean up: delete duplicates and empty
    bpy.ops.object.select_all(action='DESELECT')
    for dup in duplicates:
        mesh_data = dup.data
        bpy.data.objects.remove(dup)
        bpy.data.meshes.remove(mesh_data)

    bpy.data.objects.remove(empty)

    return True


class EXPORT_OT_collections_to_unity(bpy.types.Operator):
    bl_idname = "export.collections_to_unity"
    bl_label = "Export All Collections"
    bl_options = {'REGISTER', 'UNDO'}

    directory: bpy.props.StringProperty(
        name="Export Folder",
        subtype='DIR_PATH'
    )

    def execute(self, context):
        if not self.directory:
            self.report({'ERROR'}, "No export directory selected")
            return {'CANCELLED'}

        collections = get_collections_from_selected_objects(context)
        if not collections:
            self.report({'ERROR'}, "Select at least one object inside a collection")
            return {'CANCELLED'}

        settings = context.scene.unity_export_settings
        export_format = settings.export_format
        original_selection = context.selected_objects.copy()

        exported_count = 0
        for col in collections:
            if export_collection(context, col, self.directory, export_format):
                exported_count += 1

        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            if obj:
                obj.select_set(True)

        self.report({'INFO'}, f"Exported {exported_count} collection(s) as {export_format}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class EXPORT_OT_single_collection_to_unity(bpy.types.Operator):
    bl_idname = "export.single_collection_to_unity"
    bl_label = "Export Single Collection"
    bl_options = {'REGISTER', 'UNDO'}

    directory: bpy.props.StringProperty(
        name="Export Folder",
        subtype='DIR_PATH'
    )

    def execute(self, context):
        if not self.directory:
            self.report({'ERROR'}, "No export directory selected")
            return {'CANCELLED'}

        collections = get_collections_from_selected_objects(context)
        if not collections:
            self.report({'ERROR'}, "Select at least one object inside a collection")
            return {'CANCELLED'}

        # Use only the first collection found
        col = collections[0]
        settings = context.scene.unity_export_settings
        export_format = settings.export_format
        original_selection = context.selected_objects.copy()

        if export_collection(context, col, self.directory, export_format):
            self.report({'INFO'}, f"Exported '{col.name}' as {export_format}")
        else:
            self.report({'WARNING'}, f"No mesh objects in collection '{col.name}'")

        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            if obj:
                obj.select_set(True)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class UNITY_PT_collection_export_panel(bpy.types.Panel):
    bl_label = "Unity Export"
    bl_idname = "UNITY_PT_collection_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Unity Export'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.unity_export_settings

        layout.label(text="Select objects inside collections")

        # Format toggle
        layout.prop(settings, "export_format", expand=True)

        layout.separator()

        # Export buttons
        layout.operator(EXPORT_OT_single_collection_to_unity.bl_idname, icon='OUTLINER_COLLECTION')
        layout.operator(EXPORT_OT_collections_to_unity.bl_idname, icon='EXPORT')


def register():
    bpy.utils.register_class(UnityExportSettings)
    bpy.utils.register_class(EXPORT_OT_collections_to_unity)
    bpy.utils.register_class(EXPORT_OT_single_collection_to_unity)
    bpy.utils.register_class(UNITY_PT_collection_export_panel)
    bpy.types.Scene.unity_export_settings = bpy.props.PointerProperty(type=UnityExportSettings)


def unregister():
    bpy.utils.unregister_class(UNITY_PT_collection_export_panel)
    bpy.utils.unregister_class(EXPORT_OT_single_collection_to_unity)
    bpy.utils.unregister_class(EXPORT_OT_collections_to_unity)
    bpy.utils.unregister_class(UnityExportSettings)
    del bpy.types.Scene.unity_export_settings


if __name__ == "__main__":
    register()
