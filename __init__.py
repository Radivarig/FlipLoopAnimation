bl_info = {
    "name": "Flip Loop Animation",
    "author": "Reslav Hollos",
    "description": "Addon that automates flipping the second half of looped animations",
    "blender": (4, 1, 1),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Animation"
}

import bpy

def set_scene_frames_by_action_length(scene, action):
    scene.frame_start = 0
    scene.frame_end = int(action.frame_range.y) - 1

def depsgraph_update(scene, depsgraph):
    obj = bpy.context.active_object
    if not obj:
        print('No active object.')
        return

    action = obj.animation_data and obj.animation_data.action
    if not action:
        print(f'No action found on object: {obj.name}')
        return

    p = 'previous_action'
    if obj[p] != action.name:
        obj[p] = action.name
        set_scene_frames_by_action_length(scene, action)

def toggle_auto_set_scene_frames_onchange(self, context):
    if self.toggle_auto_set_scene_frames:
        if depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)
    else:
        if depsgraph_update in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)

class FlipLoopAnimationProperties(bpy.types.PropertyGroup):
    toggle_auto_set_scene_frames: bpy.props.BoolProperty(
        name="Auto set Start/End frames",
        description="Auto set Start frame to 0 and End frame to Animation length - 1",
        default=False,
        update=toggle_auto_set_scene_frames_onchange
    )

class DOPESHEET_PT_flip_loop_animation_panel(bpy.types.Panel):
    bl_label = "Flip Loop Animation"
    bl_idname = "DOPESHEET_PT_flip_loop_animation_panel"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Flip Loop Animation'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.prop(scene.flip_loop_animation, "toggle_auto_set_scene_frames")
        layout.operator("dopesheet.hello_operator")

class DOPESHEET_OT_hello_operator(bpy.types.Operator):
    bl_idname = "dopesheet.hello_operator"
    bl_label = "Bla"

    def execute(self, context):
        self.report({'INFO'}, "Hello World operator executed")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DOPESHEET_PT_flip_loop_animation_panel)
    bpy.utils.register_class(DOPESHEET_OT_hello_operator)
    bpy.utils.register_class(FlipLoopAnimationProperties)
    bpy.types.Scene.flip_loop_animation = bpy.props.PointerProperty(type=FlipLoopAnimationProperties)

def unregister():
    bpy.utils.unregister_class(DOPESHEET_PT_flip_loop_animation_panel)
    bpy.utils.unregister_class(DOPESHEET_OT_hello_operator)
    bpy.utils.unregister_class(FlipLoopAnimationProperties)
    del bpy.types.Scene.flip_loop_animation
    if depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)

if __name__ == "__main__":
    register()
