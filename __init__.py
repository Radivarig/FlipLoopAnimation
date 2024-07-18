bl_info = {
    'name': 'Flip Loop Animation',
    'author': 'Reslav Hollos',
    'description': '',
    'blender': (4, 1, 1),
    'version': (0, 0, 2),
    'location': '',
    'warning': '',
    'category': 'Animation'
}

import bpy
import time

# TODO: convert to a debounce wrapper
TIME_INTERVAL = 0.5
last_depsgraph_update_time = 0

def getState(scene):
    return scene.flip_loop_animation

def set_scene_frames_by_action_length(scene, action):
    scene.frame_start = 0
    scene.frame_end = int(action.frame_range.y) - 1

def on_action_changed(scene, action):
    state = getState(scene)
    print("on action changed", state.auto_set_scene_frames, state.flip_loop_active, action.name)

    if state.auto_set_scene_frames:
        set_scene_frames_by_action_length(scene, action)
    
    # on action change, stop the fliploop
    state.flip_loop_active = False

def depsgraph_update(scene, depsgraph):
    global last_depsgraph_update_time
    now = time.time()
    if now - last_depsgraph_update_time < TIME_INTERVAL:
        return
    last_depsgraph_update_time = now

    obj = bpy.context.active_object
    if not obj:
        print('No active object.')
        return

    action = obj.animation_data and obj.animation_data.action
    if not action:
        print(f'No action found on object: {obj.name}')
        return

    state = getState(scene)

    if state.last_action != action.name:
        state.last_action = action.name
        on_action_changed(scene, action)

    if state.flip_loop_active:
        handle_flip_loop(scene, action)

def handle_flip_loop(scene, action):
    print("handle_flip_loop")

class FlipLoopAnimationProperties(bpy.types.PropertyGroup):
    auto_set_scene_frames: bpy.props.BoolProperty(
        name='Auto set Start/End frames',
        description='Auto set Start frame to 0 and End frame to Animation length - 1',
        default=False
    )

    flip_loop_active: bpy.props.BoolProperty(
        name="Flip Loop Active",
        description="Toggle the Flip Loop state",
        default=False
    )

    last_action: bpy.props.StringProperty(
        name="Last Action",
        description="Store the name of the last action",
        default=""
    )

class DOPESHEET_PT_flip_loop_animation_panel(bpy.types.Panel):
    bl_label = 'Flip Loop Animation'
    bl_idname = 'DOPESHEET_PT_flip_loop_animation_panel'
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Flip Loop Animation'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        state = getState(scene)

        # NOTE: this automatically toggles the boolean regardless of the update callback
        layout.prop(state, 'auto_set_scene_frames')

        if state.flip_loop_active:
            layout.operator('dopesheet.toggle_flip_loop_operator', text='Stop Flip Loop', icon='PAUSE')
        else:
            layout.operator('dopesheet.toggle_flip_loop_operator', text='Start Flip Loop', icon='PLAY')

class DOPESHEET_OT_toggle_flip_loop_operator(bpy.types.Operator):
    bl_idname = 'dopesheet.toggle_flip_loop_operator'
    bl_label = 'Toggle Flip Loop'
    bl_description = 'While active: deletes right part of the animation, pastes left part flipped to right, duplicates first frame to last'

    def execute(self, context):
        state = getState(bpy.context.scene)
        state.flip_loop_active = not state.flip_loop_active
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DOPESHEET_PT_flip_loop_animation_panel)
    bpy.utils.register_class(DOPESHEET_OT_toggle_flip_loop_operator)
    bpy.utils.register_class(FlipLoopAnimationProperties)

    bpy.types.Scene.flip_loop_animation = bpy.props.PointerProperty(type=FlipLoopAnimationProperties)

    if depsgraph_update not in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)

def unregister():
    bpy.utils.unregister_class(DOPESHEET_PT_flip_loop_animation_panel)
    bpy.utils.unregister_class(DOPESHEET_OT_toggle_flip_loop_operator)
    bpy.utils.unregister_class(FlipLoopAnimationProperties)

    del bpy.types.Scene.flip_loop_animation

    if depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)

if __name__ == '__main__':
    register()
