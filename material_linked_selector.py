bl_info = {
    "name": "Material Linked Selector",
    "author": "Manjunath B",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > N Panel > Material",
    "description": "Select all mesh objects that share the same material as the active object",
    "category": "Object",
}

import bpy


class OBJECT_OT_select_same_material(bpy.types.Operator):
    """Select all mesh objects that use the same material as the active object"""
    bl_idname = "object.select_same_material"
    bl_label = "Select Objects With Same Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.active_object

        if active_obj is None:
            self.report({'WARNING'}, "No active object selected")
            return {'CANCELLED'}

        if active_obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a Mesh")
            return {'CANCELLED'}

        # Collect materials from active object
        active_materials = {
            slot.material
            for slot in active_obj.material_slots
            if slot.material is not None
        }

        if not active_materials:
            self.report({'WARNING'}, "Active object has no materials")
            return {'CANCELLED'}

        # Deselect everything
        bpy.ops.object.select_all(action='DESELECT')

        # Select matching objects
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material in active_materials:
                        obj.select_set(True)
                        break

        # Restore active object
        active_obj.select_set(True)
        context.view_layer.objects.active = active_obj

        return {'FINISHED'}


class VIEW3D_PT_material_linked_selector(bpy.types.Panel):
    bl_label = "Material Tools"
    bl_idname = "VIEW3D_PT_material_linked_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Material"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Selection")
        layout.operator(
            "object.select_same_material",
            icon='MATERIAL'
        )


classes = (
    OBJECT_OT_select_same_material,
    VIEW3D_PT_material_linked_selector,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
