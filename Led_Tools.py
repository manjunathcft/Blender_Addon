bl_info = {
    "name": "LED Curve Generator",
    "author": "Gemini / ChatGPT",
    "version": (1, 21, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > LED Tools",
    "description": "Instance LED pixels along a selected curve with advanced mapping controls including rotation. Compatible with Blender 4.5+",
    "category": "Object",
}

import bpy
import math

def set_node_mode(node, mode_value):
    """Sets the mode of a node, handling API changes in newer Blender versions."""
    # Try standard property (Blender < 5.0 behavior for most nodes)
    if hasattr(node, 'mode'):
        try:
            node.mode = mode_value
            return
        except TypeError:
            pass # Value might be invalid for property, try input?

    # Try Input Socket (Blender 5.0+ / Menu Socket behavior)
    # "Mode" is the standard name for the input socket if it was converted
    if "Mode" in node.inputs:
        try:
            node.inputs["Mode"].default_value = mode_value
            return
        except Exception:
            pass
            
    # Fallback: Check for 'operation' property (some nodes use this)
    if hasattr(node, 'operation'):
        try:
            node.operation = mode_value
            return
        except Exception:
            pass

def setup_material_nodes(mat):
    """Sets up a procedural animated test pattern for the material with a rotation control."""
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Output
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (500, 0)
    
    # Principled BSDF
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (200, 0)
    principled.inputs["Emission Strength"].default_value = 5.0
    
    # UV Map Node
    uv_map_node = nodes.new("ShaderNodeUVMap")
    uv_map_node.location = (-1100, 0)
    uv_map_node.uv_map = "UVMap"
    
    # Vector Rotate for Mapping Rotation
    vec_rotate = nodes.new("ShaderNodeVectorRotate")
    vec_rotate.name = "MAPPING_ROTATION_NODE"
    vec_rotate.rotation_type = 'EULER_XYZ'
    vec_rotate.location = (-900, 0)
    vec_rotate.inputs["Center"].default_value = (0.5, 0.5, 0.5)
    links.new(uv_map_node.outputs["UV"], vec_rotate.inputs["Vector"])
    
    # Time Driver
    value_time = nodes.new("ShaderNodeValue")
    value_time.location = (-900, 200)
    value_time.label = "Time (Frame/100)"
    d = value_time.outputs[0].driver_add("default_value")
    d.driver.expression = "frame / 100.0"
    
    # Vector Math (Add Time to UV to animate)
    vec_add = nodes.new("ShaderNodeVectorMath")
    vec_add.location = (-700, 0)
    vec_add.operation = 'ADD'
    links.new(vec_rotate.outputs["Vector"], vec_add.inputs[0])
    links.new(value_time.outputs[0], vec_add.inputs[1])
    
    # Wave Texture
    wave_tex = nodes.new("ShaderNodeTexWave")
    wave_tex.location = (-500, 0)
    wave_tex.wave_type = 'BANDS'
    wave_tex.bands_direction = 'X'
    wave_tex.inputs["Scale"].default_value = 2.0
    
    # Color Ramp
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].color = (0, 0.1, 1, 1)
    color_ramp.color_ramp.elements[1].color = (1, 0.5, 0, 1)
    
    # Image Texture (Disconnected)
    image_texture = nodes.new("ShaderNodeTexImage")
    image_texture.location = (-500, 300)
    image_texture.label = "Connect Video Here"
    
    # Links
    links.new(vec_add.outputs["Vector"], wave_tex.inputs["Vector"])
    links.new(wave_tex.outputs["Color"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], principled.inputs["Emission Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

def build_geometry_nodes(obj):
    # Setup
    mod = obj.modifiers.get("LED_Curve_GN")
    if not mod:
        mod = obj.modifiers.new("LED_Curve_GN", 'NODES')
    
    ng = mod.node_group
    if not ng:
        ng = bpy.data.node_groups.new(f"{obj.name}_GN_Tree", 'GeometryNodeTree')
        mod.node_group = ng

    nodes = ng.nodes
    links = ng.links
    nodes.clear()

    # -------------------------
    # 0. Interface
    # -------------------------
    iface = ng.interface
    iface.clear()

    iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    iface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    iface.new_socket("LED Pixel", in_out='INPUT', socket_type='NodeSocketObject')
    
    iface.new_socket("Use Spacing", in_out='INPUT', socket_type='NodeSocketBool').default_value = False
    iface.new_socket("LED Count", in_out='INPUT', socket_type='NodeSocketInt').default_value = 50
    iface.new_socket("LED Spacing", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.1
    
    iface.new_socket("Strip Count", in_out='INPUT', socket_type='NodeSocketInt').default_value = 1
    iface.new_socket("Use Custom Path", in_out='INPUT', socket_type='NodeSocketBool').default_value = False
    iface.new_socket("Custom Path", in_out='INPUT', socket_type='NodeSocketObject')
    iface.new_socket("Radial Radius", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 1.0
    iface.new_socket("Radial Axis (0:Z, 1:X, 2:Y)", in_out='INPUT', socket_type='NodeSocketInt').default_value = 0
    
    iface.new_socket("Optimize Viewport", in_out='INPUT', socket_type='NodeSocketBool').default_value = True
    iface.new_socket("Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    
    iface.new_socket("Mapping Mode (0:Grid, 1:Planar, 2:Cylindrical)", in_out='INPUT', socket_type='NodeSocketInt').default_value = 0
    iface.new_socket("Mapping Scale", in_out='INPUT', socket_type='NodeSocketVector').default_value = (1.0, 1.0, 1.0)
    iface.new_socket("Mapping Rotation", in_out='INPUT', socket_type='NodeSocketVector').default_value = (0.0, 0.0, 0.0)

    # -------------------------
    # 1. Nodes Setup
    # -------------------------
    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-2600, 0)
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (2800, 0)

    # =========================================
    # PART A: SOURCE STRIP PREPARATION
    # =========================================
    resample_count = nodes.new("GeometryNodeResampleCurve")
    resample_count.location = (-2300, 200)
    set_node_mode(resample_count, 'COUNT') # FIX: Use helper
    links.new(group_in.outputs["Geometry"], resample_count.inputs["Curve"])
    links.new(group_in.outputs["LED Count"], resample_count.inputs["Count"])

    resample_length = nodes.new("GeometryNodeResampleCurve")
    resample_length.location = (-2300, -100)
    set_node_mode(resample_length, 'LENGTH') # FIX: Use helper
    links.new(group_in.outputs["Geometry"], resample_length.inputs["Curve"])
    links.new(group_in.outputs["LED Spacing"], resample_length.inputs["Length"])

    switch_resample = nodes.new("GeometryNodeSwitch")
    switch_resample.location = (-2100, 0)
    switch_resample.input_type = 'GEOMETRY'
    links.new(group_in.outputs["Use Spacing"], switch_resample.inputs["Switch"])
    links.new(resample_count.outputs["Curve"], switch_resample.inputs["False"])
    links.new(resample_length.outputs["Curve"], switch_resample.inputs["True"])

    spline_param = nodes.new("GeometryNodeSplineParameter")
    spline_param.location = (-2100, 300)
    
    store_u = nodes.new("GeometryNodeStoreNamedAttribute")
    store_u.location = (-1900, 0)
    store_u.data_type = 'FLOAT'
    store_u.domain = 'POINT'
    store_u.inputs["Name"].default_value = "U_Val"
    links.new(switch_resample.outputs["Output"], store_u.inputs["Geometry"])
    links.new(spline_param.outputs["Factor"], store_u.inputs["Value"])

    curve_to_points = nodes.new("GeometryNodeCurveToPoints")
    curve_to_points.location = (-1700, 0)
    set_node_mode(curve_to_points, 'EVALUATED') # FIX: Use helper
    links.new(store_u.outputs["Geometry"], curve_to_points.inputs["Curve"])

    store_base_rot = nodes.new("GeometryNodeStoreNamedAttribute")
    store_base_rot.location = (-1500, 0)
    store_base_rot.data_type = 'FLOAT_VECTOR'
    store_base_rot.domain = 'POINT'
    store_base_rot.inputs["Name"].default_value = "BaseRot"
    links.new(curve_to_points.outputs["Points"], store_base_rot.inputs["Geometry"])
    links.new(curve_to_points.outputs["Rotation"], store_base_rot.inputs["Value"])

    pos_node = nodes.new("GeometryNodeInputPosition")
    pos_node.location = (-1500, 200)
    
    store_strip_pos = nodes.new("GeometryNodeStoreNamedAttribute")
    store_strip_pos.location = (-1300, 0)
    store_strip_pos.data_type = 'FLOAT_VECTOR'
    store_strip_pos.domain = 'POINT'
    store_strip_pos.inputs["Name"].default_value = "StripPos"
    links.new(store_base_rot.outputs["Geometry"], store_strip_pos.inputs["Geometry"])
    links.new(pos_node.outputs["Position"], store_strip_pos.inputs["Value"])

    source_points = store_strip_pos

    # =========================================
    # PART B: ANCHOR PATH GENERATION
    # =========================================
    obj_info = nodes.new("GeometryNodeObjectInfo")
    obj_info.location = (-2300, -500)
    obj_info.transform_space = 'RELATIVE'
    links.new(group_in.outputs["Custom Path"], obj_info.inputs["Object"])
    
    realize_path = nodes.new("GeometryNodeRealizeInstances")
    realize_path.location = (-2100, -500)
    links.new(obj_info.outputs["Geometry"], realize_path.inputs["Geometry"])
    
    resample_path = nodes.new("GeometryNodeResampleCurve")
    resample_path.location = (-1900, -500)
    set_node_mode(resample_path, 'COUNT') # FIX: Use helper
    links.new(realize_path.outputs["Geometry"], resample_path.inputs["Curve"])
    links.new(group_in.outputs["Strip Count"], resample_path.inputs["Count"])

    curve_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    curve_circle.location = (-2300, -800)
    links.new(group_in.outputs["Radial Radius"], curve_circle.inputs["Radius"])
    links.new(group_in.outputs["Strip Count"], curve_circle.inputs["Resolution"])

    trans_x = nodes.new("GeometryNodeTransform")
    trans_x.location = (-2100, -700)
    trans_x.inputs["Rotation"].default_value = (0, 1.5708, 0)
    links.new(curve_circle.outputs["Curve"], trans_x.inputs["Geometry"])

    trans_y = nodes.new("GeometryNodeTransform")
    trans_y.location = (-2100, -900)
    trans_y.inputs["Rotation"].default_value = (1.5708, 0, 0)
    links.new(curve_circle.outputs["Curve"], trans_y.inputs["Geometry"])

    compare_x = nodes.new("FunctionNodeCompare")
    compare_x.location = (-1900, -650)
    compare_x.data_type = 'INT'
    compare_x.operation = 'EQUAL'
    links.new(group_in.outputs["Radial Axis (0:Z, 1:X, 2:Y)"], compare_x.inputs["A"])
    compare_x.inputs["B"].default_value = 1

    switch_x_z = nodes.new("GeometryNodeSwitch")
    switch_x_z.location = (-1700, -750)
    switch_x_z.input_type = 'GEOMETRY'
    links.new(compare_x.outputs["Result"], switch_x_z.inputs["Switch"])
    links.new(curve_circle.outputs["Curve"], switch_x_z.inputs["False"])
    links.new(trans_x.outputs["Geometry"], switch_x_z.inputs["True"])

    compare_y = nodes.new("FunctionNodeCompare")
    compare_y.location = (-1900, -850)
    compare_y.data_type = 'INT'
    compare_y.operation = 'EQUAL'
    links.new(group_in.outputs["Radial Axis (0:Z, 1:X, 2:Y)"], compare_y.inputs["A"])
    compare_y.inputs["B"].default_value = 2

    switch_y_final = nodes.new("GeometryNodeSwitch")
    switch_y_final.location = (-1500, -800)
    switch_y_final.input_type = 'GEOMETRY'
    links.new(compare_y.outputs["Result"], switch_y_final.inputs["Switch"])
    links.new(switch_x_z.outputs["Output"], switch_y_final.inputs["False"])
    links.new(trans_y.outputs["Geometry"], switch_y_final.inputs["True"])

    switch_path = nodes.new("GeometryNodeSwitch")
    switch_path.location = (-1300, -600)
    switch_path.input_type = 'GEOMETRY'
    links.new(group_in.outputs["Use Custom Path"], switch_path.inputs["Switch"])
    links.new(switch_y_final.outputs["Output"], switch_path.inputs["False"])
    links.new(resample_path.outputs["Curve"], switch_path.inputs["True"])

    anchor_points = nodes.new("GeometryNodeCurveToPoints")
    anchor_points.location = (-1100, -600)
    set_node_mode(anchor_points, 'EVALUATED') # FIX: Use helper
    links.new(switch_path.outputs["Output"], anchor_points.inputs["Curve"])

    index_node = nodes.new("GeometryNodeInputIndex")
    index_node.location = (-1300, -900)
    
    math_count_sub_1 = nodes.new("ShaderNodeMath")
    math_count_sub_1.location = (-1300, -1000)
    math_count_sub_1.operation = 'SUBTRACT'
    links.new(group_in.outputs["Strip Count"], math_count_sub_1.inputs[0])
    math_count_sub_1.inputs[1].default_value = 1.0
    
    math_max_1 = nodes.new("ShaderNodeMath")
    math_max_1.location = (-1100, -1000)
    math_max_1.operation = 'MAXIMUM'
    links.new(math_count_sub_1.outputs[0], math_max_1.inputs[0])
    math_max_1.inputs[1].default_value = 1.0

    math_div_v = nodes.new("ShaderNodeMath")
    math_div_v.location = (-900, -900)
    math_div_v.operation = 'DIVIDE'
    links.new(index_node.outputs["Index"], math_div_v.inputs[0])
    links.new(math_max_1.outputs[0], math_div_v.inputs[1])

    compare_single = nodes.new("FunctionNodeCompare")
    compare_single.location = (-900, -1100)
    compare_single.data_type = 'INT'
    compare_single.operation = 'EQUAL'
    links.new(group_in.outputs["Strip Count"], compare_single.inputs["A"])
    compare_single.inputs["B"].default_value = 1

    switch_v = nodes.new("GeometryNodeSwitch")
    switch_v.location = (-700, -900)
    switch_v.input_type = 'FLOAT'
    links.new(compare_single.outputs["Result"], switch_v.inputs["Switch"])
    links.new(math_div_v.outputs[0], switch_v.inputs["False"])
    switch_v.inputs["True"].default_value = 0.5

    store_v_anchors = nodes.new("GeometryNodeStoreNamedAttribute")
    store_v_anchors.location = (-500, -600)
    store_v_anchors.data_type = 'FLOAT'
    store_v_anchors.domain = 'POINT'
    store_v_anchors.inputs["Name"].default_value = "V_Val"
    links.new(anchor_points.outputs["Points"], store_v_anchors.inputs["Geometry"])
    links.new(switch_v.outputs["Output"], store_v_anchors.inputs["Value"])

    store_anchor_rot_on_anchors = nodes.new("GeometryNodeStoreNamedAttribute")
    store_anchor_rot_on_anchors.location = (-300, -600)
    store_anchor_rot_on_anchors.data_type = 'FLOAT_VECTOR'
    store_anchor_rot_on_anchors.domain = 'POINT'
    store_anchor_rot_on_anchors.inputs["Name"].default_value = "StoredAnchorRot"
    links.new(store_v_anchors.outputs["Geometry"], store_anchor_rot_on_anchors.inputs["Geometry"])
    links.new(anchor_points.outputs["Rotation"], store_anchor_rot_on_anchors.inputs["Value"])
    
    anchor_geometry = store_anchor_rot_on_anchors

    # =========================================
    # PART C: DUPLICATION & POSITIONING
    # =========================================
    duplicate = nodes.new("GeometryNodeDuplicateElements")
    duplicate.location = (-1000, 0)
    duplicate.domain = 'POINT'
    links.new(source_points.outputs["Geometry"], duplicate.inputs["Geometry"])
    links.new(group_in.outputs["Strip Count"], duplicate.inputs["Amount"])

    sample_anchor_pos = nodes.new("GeometryNodeSampleIndex")
    sample_anchor_pos.location = (-700, -200)
    sample_anchor_pos.domain = 'POINT'
    sample_anchor_pos.data_type = 'FLOAT_VECTOR'
    links.new(anchor_geometry.outputs["Geometry"], sample_anchor_pos.inputs["Geometry"])
    links.new(duplicate.outputs["Duplicate Index"], sample_anchor_pos.inputs["Index"])
    input_pos_node = nodes.new("GeometryNodeInputPosition")
    input_pos_node.location = (-900, -200)
    links.new(input_pos_node.outputs["Position"], sample_anchor_pos.inputs["Value"])

    sample_anchor_rot = nodes.new("GeometryNodeSampleIndex")
    sample_anchor_rot.location = (-700, -400)
    sample_anchor_rot.domain = 'POINT'
    sample_anchor_rot.data_type = 'FLOAT_VECTOR'
    links.new(anchor_geometry.outputs["Geometry"], sample_anchor_rot.inputs["Geometry"])
    links.new(duplicate.outputs["Duplicate Index"], sample_anchor_rot.inputs["Index"])
    input_anchor_rot = nodes.new("GeometryNodeInputNamedAttribute")
    input_anchor_rot.location = (-900, -400)
    input_anchor_rot.data_type = 'FLOAT_VECTOR'
    input_anchor_rot.inputs["Name"].default_value = "StoredAnchorRot"
    links.new(input_anchor_rot.outputs["Attribute"], sample_anchor_rot.inputs["Value"])

    sample_v = nodes.new("GeometryNodeSampleIndex")
    sample_v.location = (-700, -600)
    sample_v.domain = 'POINT'
    sample_v.data_type = 'FLOAT'
    links.new(anchor_geometry.outputs["Geometry"], sample_v.inputs["Geometry"])
    links.new(duplicate.outputs["Duplicate Index"], sample_v.inputs["Index"])
    input_v = nodes.new("GeometryNodeInputNamedAttribute")
    input_v.location = (-900, -600)
    input_v.data_type = 'FLOAT'
    input_v.inputs["Name"].default_value = "V_Val"
    links.new(input_v.outputs["Attribute"], sample_v.inputs["Value"])

    store_v_final = nodes.new("GeometryNodeStoreNamedAttribute")
    store_v_final.location = (-400, 0)
    store_v_final.data_type = 'FLOAT'
    store_v_final.domain = 'POINT'
    store_v_final.inputs["Name"].default_value = "V_Val"
    links.new(duplicate.outputs["Geometry"], store_v_final.inputs["Geometry"])
    links.new(sample_v.outputs["Value"], store_v_final.inputs["Value"])

    get_strip_pos = nodes.new("GeometryNodeInputNamedAttribute")
    get_strip_pos.location = (-700, 200)
    get_strip_pos.data_type = 'FLOAT_VECTOR'
    get_strip_pos.inputs["Name"].default_value = "StripPos"
    
    vec_rot = nodes.new("ShaderNodeVectorRotate")
    vec_rot.location = (-400, 200)
    vec_rot.rotation_type = 'EULER_XYZ'
    links.new(get_strip_pos.outputs["Attribute"], vec_rot.inputs["Vector"])
    links.new(sample_anchor_rot.outputs["Value"], vec_rot.inputs["Rotation"])
    
    vec_add_pos = nodes.new("ShaderNodeVectorMath")
    vec_add_pos.location = (-200, 200)
    vec_add_pos.operation = 'ADD'
    links.new(sample_anchor_pos.outputs["Value"], vec_add_pos.inputs[0])
    links.new(vec_rot.outputs["Vector"], vec_add_pos.inputs[1])
    
    set_pos = nodes.new("GeometryNodeSetPosition")
    set_pos.location = (0, 0)
    links.new(store_v_final.outputs["Geometry"], set_pos.inputs["Geometry"])
    links.new(vec_add_pos.outputs["Vector"], set_pos.inputs["Position"])

    get_base_rot = nodes.new("GeometryNodeInputNamedAttribute")
    get_base_rot.location = (-400, 400)
    get_base_rot.data_type = 'FLOAT_VECTOR'
    get_base_rot.inputs["Name"].default_value = "BaseRot"
    
    rot_euler = nodes.new("FunctionNodeRotateEuler")
    rot_euler.location = (-200, 400)
    rot_euler.space = 'OBJECT'
    links.new(get_base_rot.outputs["Attribute"], rot_euler.inputs["Rotation"])
    links.new(sample_anchor_rot.outputs["Value"], rot_euler.inputs["Rotate By"])
    
    store_final_rot = nodes.new("GeometryNodeStoreNamedAttribute")
    store_final_rot.location = (200, 0)
    store_final_rot.data_type = 'FLOAT_VECTOR'
    store_final_rot.domain = 'POINT'
    store_final_rot.inputs["Name"].default_value = "FinalRot"
    links.new(set_pos.outputs["Geometry"], store_final_rot.inputs["Geometry"])
    links.new(rot_euler.outputs["Rotation"], store_final_rot.inputs["Value"])

    # =========================================
    # PART D: UV MAPPING
    # =========================================
    get_u = nodes.new("GeometryNodeInputNamedAttribute")
    get_u.location = (400, 400)
    get_u.data_type = 'FLOAT'
    get_u.inputs["Name"].default_value = "U_Val"
    
    get_v = nodes.new("GeometryNodeInputNamedAttribute")
    get_v.location = (400, 300)
    get_v.data_type = 'FLOAT'
    get_v.inputs["Name"].default_value = "V_Val"
    
    combine_uv_grid = nodes.new("ShaderNodeCombineXYZ")
    combine_uv_grid.location = (600, 350)
    links.new(get_u.outputs["Attribute"], combine_uv_grid.inputs["X"])
    links.new(get_v.outputs["Attribute"], combine_uv_grid.inputs["Y"])

    final_pos = nodes.new("GeometryNodeInputPosition")
    final_pos.location = (400, 100)
    
    scale_pos = nodes.new("ShaderNodeVectorMath")
    scale_pos.location = (600, 100)
    scale_pos.operation = 'MULTIPLY'
    links.new(final_pos.outputs["Position"], scale_pos.inputs[0])
    links.new(group_in.outputs["Mapping Scale"], scale_pos.inputs[1])
    
    sep_xyz = nodes.new("ShaderNodeSeparateXYZ")
    sep_xyz.location = (800, -100)
    links.new(scale_pos.outputs["Vector"], sep_xyz.inputs[0])
    
    math_atan2 = nodes.new("ShaderNodeMath")
    math_atan2.location = (1000, -50)
    math_atan2.operation = 'ARCTAN2'
    links.new(sep_xyz.outputs["Y"], math_atan2.inputs[0])
    links.new(sep_xyz.outputs["X"], math_atan2.inputs[1])
    
    map_range_u = nodes.new("ShaderNodeMapRange")
    map_range_u.location = (1200, -50)
    map_range_u.inputs["From Min"].default_value = -math.pi
    map_range_u.inputs["From Max"].default_value = math.pi
    links.new(math_atan2.outputs[0], map_range_u.inputs["Value"])
    
    map_range_v = nodes.new("ShaderNodeMapRange")
    map_range_v.location = (1200, -200)
    links.new(sep_xyz.outputs["Z"], map_range_v.inputs["Value"])
    
    combine_uv_cyl = nodes.new("ShaderNodeCombineXYZ")
    combine_uv_cyl.location = (1400, -100)
    links.new(map_range_u.outputs["Result"], combine_uv_cyl.inputs["X"])
    links.new(map_range_v.outputs["Result"], combine_uv_cyl.inputs["Y"])

    compare_planar = nodes.new("FunctionNodeCompare")
    compare_planar.location = (800, 200)
    compare_planar.data_type = 'INT'
    compare_planar.operation = 'EQUAL'
    links.new(group_in.outputs["Mapping Mode (0:Grid, 1:Planar, 2:Cylindrical)"], compare_planar.inputs["A"])
    compare_planar.inputs["B"].default_value = 1

    switch_planar = nodes.new("GeometryNodeSwitch")
    switch_planar.location = (1000, 300)
    switch_planar.input_type = 'VECTOR'
    links.new(compare_planar.outputs["Result"], switch_planar.inputs["Switch"])
    links.new(combine_uv_grid.outputs["Vector"], switch_planar.inputs["False"])
    links.new(scale_pos.outputs["Vector"], switch_planar.inputs["True"])

    compare_cyl = nodes.new("FunctionNodeCompare")
    compare_cyl.location = (1400, 100)
    compare_cyl.data_type = 'INT'
    compare_cyl.operation = 'EQUAL'
    links.new(group_in.outputs["Mapping Mode (0:Grid, 1:Planar, 2:Cylindrical)"], compare_cyl.inputs["A"])
    compare_cyl.inputs["B"].default_value = 2

    switch_final_map = nodes.new("GeometryNodeSwitch")
    switch_final_map.location = (1600, 200)
    switch_final_map.input_type = 'VECTOR'
    links.new(compare_cyl.outputs["Result"], switch_final_map.inputs["Switch"])
    links.new(switch_planar.outputs["Output"], switch_final_map.inputs["False"])
    links.new(combine_uv_cyl.outputs["Vector"], switch_final_map.inputs["True"])

    store_grid_uv = nodes.new("GeometryNodeStoreNamedAttribute")
    store_grid_uv.location = (1800, 0)
    store_grid_uv.data_type = 'FLOAT_VECTOR'
    store_grid_uv.domain = 'POINT'
    store_grid_uv.inputs["Name"].default_value = "GridUV"
    links.new(store_final_rot.outputs["Geometry"], store_grid_uv.inputs["Geometry"])
    links.new(switch_final_map.outputs["Output"], store_grid_uv.inputs["Value"])

    # =========================================
    # PART E: INSTANCING
    # =========================================
    obj_info_led = nodes.new("GeometryNodeObjectInfo")
    obj_info_led.location = (1800, -500)
    links.new(group_in.outputs["LED Pixel"], obj_info_led.inputs["Object"])

    cube_proxy = nodes.new("GeometryNodeMeshCube")
    cube_proxy.location = (1800, -700)
    cube_proxy.inputs["Size"].default_value = (0.02, 0.02, 0.02)

    is_viewport = nodes.new("GeometryNodeIsViewport")
    is_viewport.location = (2000, -700)

    logic_and = nodes.new("FunctionNodeBooleanMath")
    logic_and.location = (2200, -700)
    logic_and.operation = 'AND'
    links.new(group_in.outputs["Optimize Viewport"], logic_and.inputs[0])
    links.new(is_viewport.outputs[0], logic_and.inputs[1])

    switch_instance = nodes.new("GeometryNodeSwitch")
    switch_instance.location = (2400, -500)
    switch_instance.input_type = 'GEOMETRY'
    links.new(logic_and.outputs["Boolean"], switch_instance.inputs["Switch"])
    links.new(obj_info_led.outputs["Geometry"], switch_instance.inputs["False"])
    links.new(cube_proxy.outputs["Mesh"], switch_instance.inputs["True"])

    get_final_rot = nodes.new("GeometryNodeInputNamedAttribute")
    get_final_rot.location = (2000, -300)
    get_final_rot.data_type = 'FLOAT_VECTOR'
    get_final_rot.inputs["Name"].default_value = "FinalRot"

    instance_leds = nodes.new("GeometryNodeInstanceOnPoints")
    instance_leds.location = (2600, 0)
    links.new(store_grid_uv.outputs["Geometry"], instance_leds.inputs["Points"])
    links.new(switch_instance.outputs["Output"], instance_leds.inputs["Instance"])
    links.new(get_final_rot.outputs["Attribute"], instance_leds.inputs["Rotation"])

    realize_final = nodes.new("GeometryNodeRealizeInstances")
    realize_final.location = (2800, 0)
    links.new(instance_leds.outputs["Instances"], realize_final.inputs["Geometry"])

    copy_uv_to_corner = nodes.new("GeometryNodeStoreNamedAttribute")
    copy_uv_to_corner.location = (3000, 200)
    copy_uv_to_corner.data_type = 'FLOAT_VECTOR'
    copy_uv_to_corner.domain = 'CORNER'
    copy_uv_to_corner.inputs["Name"].default_value = "UVMap"
    
    read_grid_uv = nodes.new("GeometryNodeInputNamedAttribute")
    read_grid_uv.location = (2800, 200)
    read_grid_uv.data_type = 'FLOAT_VECTOR'
    read_grid_uv.inputs["Name"].default_value = "GridUV"
    
    links.new(realize_final.outputs["Geometry"], copy_uv_to_corner.inputs["Geometry"])
    links.new(read_grid_uv.outputs["Attribute"], copy_uv_to_corner.inputs["Value"])

    set_material = nodes.new("GeometryNodeSetMaterial")
    set_material.location = (3200, 0)
    links.new(copy_uv_to_corner.outputs["Geometry"], set_material.inputs["Geometry"])
    links.new(group_in.outputs["Material"], set_material.inputs["Material"])

    links.new(set_material.outputs["Geometry"], group_out.inputs["Geometry"])


class ApplyLedToCurve(bpy.types.Operator):
    bl_idname = "object.apply_led_to_curve"
    bl_label = "Apply LEDs to Selected Curve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
        
        if not selected_curves:
            self.report({'ERROR'}, "No Curve objects selected.")
            return {'CANCELLED'}

        original_active = context.view_layer.objects.active
        
        led_pixel = bpy.data.objects.get("LED_PIXEL")

        if led_pixel and led_pixel.name == "LED_PIXEL" and led_pixel.hide_viewport:
            led_pixel.hide_viewport = False
            led_pixel.hide_render = False
            self.report({'INFO'}, "Unhiding existing 'LED_PIXEL' object.")

        if not led_pixel:
            bpy.ops.mesh.primitive_cube_add(size=0.05)
            led_pixel = context.active_object
            led_pixel.name = "LED_PIXEL"
            led_pixel.location = (5, 5, 5)
            self.report({'INFO'}, "Created placeholder 'LED_PIXEL' cube.")
            context.view_layer.objects.active = original_active
            for curve in selected_curves:
                curve.select_set(True)

        for obj in selected_curves:
            mat_name = f"{obj.name}_LED_Material"
            new_mat = bpy.data.materials.new(name=mat_name)
            setup_material_nodes(new_mat)

            build_geometry_nodes(obj)

            mod = obj.modifiers.get("LED_Curve_GN")
            if not mod:
                continue

            mod["LED Pixel"] = led_pixel
            mod["Use Spacing"] = False
            mod["LED Count"] = 180
            mod["LED Spacing"] = 0.1
            mod["Strip Count"] = 10
            mod["Use Custom Path"] = False
            mod["Radial Radius"] = 1.0
            mod["Radial Axis (0:Z, 1:X, 2:Y)"] = 0
            mod["Optimize Viewport"] = True
            mod["Material"] = new_mat
            mod["Mapping Mode (0:Grid, 1:Planar, 2:Cylindrical)"] = 2
            mod["Mapping Scale"] = (1.0, 1.0, 1.0)
            mod["Mapping Rotation"] = (0.0, 0.0, 0.0)
            
            # --- Create the Driver ---
            rot_node = new_mat.node_tree.nodes.get("MAPPING_ROTATION_NODE")
            if rot_node:
                # driver_add on a vector returns a list of FCurves (for X, Y, Z)
                fcurves = rot_node.inputs["Rotation"].driver_add("default_value")
                for i, fcurve in enumerate(fcurves):
                    var = fcurve.driver.variables.new()
                    var.name = "mapping_rot"
                    var.targets[0].id_type = 'OBJECT'
                    var.targets[0].id = obj
                    var.targets[0].data_path = f'modifiers["{mod.name}"]["Mapping Rotation"]'
                    # Set expression to access the correct component of the vector
                    fcurve.driver.expression = f"mapping_rot[{i}]"

        self.report({'INFO'}, f"LEDs applied to {len(selected_curves)} curves. Defaulted to Cylindrical Mapping.")
        return {'FINISHED'}

class LedToolsPanel(bpy.types.Panel):
    bl_label = "LED Curve Tools"
    bl_idname = "VIEW3D_PT_led_curve_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LED Tools"

    def draw(self, _context):
        layout = self.layout
        layout.operator("object.apply_led_to_curve", icon='CURVE_DATA')

def register():
    bpy.utils.register_class(ApplyLedToCurve)
    bpy.utils.register_class(LedToolsPanel)

def unregister():
    bpy.utils.unregister_class(ApplyLedToCurve)
    bpy.utils.unregister_class(LedToolsPanel)

if __name__ == "__main__":
    register()