bl_info = {
    'name': 'Flip Loop Animation',
    'author': 'Reslav Hollós',
    'description': 'Blender tool for cyclic locomotion animations',
    'blender': (4, 1, 1),
    'version': (0, 1, 0),
    'location': 'Dope Sheet > N Panel',
    'category': 'Animation'
}

import bpy

def delete_frame_range(action, start_frame, end_frame):
    for fcurve in action.fcurves:
        # NOTE: round keyframes frame to avoid floating point errors
        indices_to_remove = [i for i, k in enumerate(fcurve.keyframe_points) if start_frame <= round(k.co[0]) <= end_frame]
        # NOTE: delete backwards to not alter list indexing
        for index in sorted(indices_to_remove, reverse=True):
            fcurve.keyframe_points.remove(fcurve.keyframe_points[index])

def copy_paste_flipped_keyframes(start_frame, target_frame):
    bpy.context.scene.frame_set(start_frame)
    # NOTE: order matters here
    bpy.ops.pose.select_all(action = 'SELECT')
    bpy.ops.anim.channels_select_all(action='SELECT')
    bpy.ops.action.select_all(action = 'SELECT')

    bpy.ops.action.copy()
    bpy.context.scene.frame_set(target_frame)
    bpy.ops.action.paste(flipped=True)

def copy_paste_one_frame(src_frame, dest_frame):
    bpy.context.scene.frame_set(src_frame)
    # NOTE: order matters here
    bpy.ops.pose.select_all(action = 'SELECT')
    bpy.ops.anim.channels_select_all(action='SELECT')
    bpy.ops.action.select_all(action = 'DESELECT')
    bpy.ops.action.select_column(mode = 'CFRA')

    bpy.ops.action.copy()
    bpy.context.scene.frame_set(dest_frame)
    bpy.ops.action.paste()

def restore_current_frame(func):
    def wrapped():
        frame = bpy.context.scene.frame_current
        result = func()
        bpy.context.scene.frame_set(frame)
        return result
    return wrapped

def restore_bone_selection(func):
    def wrapped():
        obj = bpy.context.object
        selected_bones = [bone.name for bone in obj.pose.bones if bone.bone.select]
        active_bone = obj.data.bones.active
        result = func()
        bpy.ops.pose.select_all(action = 'DESELECT')
        for bone_name in selected_bones:
            obj.data.bones[bone_name].select = True
        obj.data.bones.active = active_bone
        return result
    return wrapped

def with_dopesheet_context(func):
    def wrapped():
        context_override = bpy.context.copy()
        context_override['area'] = next(area for area in bpy.context.screen.areas if area.type == 'DOPESHEET_EDITOR')
        context_override['region'] = next(region for region in context_override['area'].regions if region.type == 'WINDOW')
        context_override['space_data'] = next(space for space in context_override['area'].spaces if space.type == 'DOPESHEET_EDITOR')
        with bpy.context.temp_override(**context_override):
            result = func()
        return result
    return wrapped
#
def getState(scene):
    return scene.flip_loop_animation

#TODO: @restore_keyframes_selection
#TODO: @restore_channels_selection
@restore_bone_selection
@restore_current_frame
@with_dopesheet_context
def handle_flip_loop():
    obj = bpy.context.object
    if obj.mode != 'POSE': bpy.ops.object.posemode_toggle()

    action = obj.animation_data.action
    action_length = int(action.frame_range[1])
    midpoint = action_length // 2

    delete_frame_range(action, midpoint, action_length)
    copy_paste_flipped_keyframes(0, midpoint)
    copy_paste_one_frame(0, action_length)

    print('handle_flip_loop')

def set_scene_frames_by_action_length(scene, action):
    scene.frame_start = 0
    scene.frame_end = int(action.frame_range.y) - 1

def on_action_changed(scene, action):
    state = getState(scene)

    if state.auto_set_scene_frames:
        set_scene_frames_by_action_length(scene, action)

    # on action change, stop the fliploop
    state.flip_loop_active = False

# TODO: add a debounce wrapper
def depsgraph_update(scene, depsgraph):

    obj = bpy.context.active_object
    if not obj: return print('No active object.')

    state = getState(scene)
    if state.auto_switch_to_nla_solo_action:
        handle_switch_to_nla_solo_action(obj)

    action = obj.animation_data and obj.animation_data.action
    if not action: return print(f'No action found on object: {obj.name}')

    if state.last_action != action.name:
        state.last_action = action.name
        on_action_changed(scene, action)

    # if state.flip_loop_active:
    #     # TODO: cancel move operator which crashes blender
    #     # handle_flip_loop()
    #     # TODO: avoid recursion by unregistering the handler during changes
    #     state.flip_loop_active = False


class FlipLoopAnimationProperties(bpy.types.PropertyGroup):
    auto_set_scene_frames: bpy.props.BoolProperty(
        name='Auto set Start/End frames',
        description='Auto set Start frame to 0 and End frame to Animation length - 1',
        default=False
    )

    auto_switch_to_nla_solo_action: bpy.props.BoolProperty(
        name='Auto switch to NLA ★ action',
        description='If NLA track is solo (★ starred), switch to the action with the same name if found',
        default=False
    )

    flip_loop_active: bpy.props.BoolProperty(
        name='Flip Loop Active',
        description='Toggle the Flip Loop state',
        default=False
    )

    last_action: bpy.props.StringProperty(
        name='Last Action',
        description='Store the name of the last action',
        default=''
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

        layout.prop(state, 'auto_set_scene_frames')
        layout.prop(state, 'auto_switch_to_nla_solo_action')

        layout.operator('dopesheet.flip_loop_operator', text='Apply Flip Loop')

        # if state.flip_loop_active:
        #     layout.operator('dopesheet.toggle_flip_loop_operator', text='Stop Flip Loop', icon='PAUSE')
        # else:
        #     layout.operator('dopesheet.toggle_flip_loop_operator', text='Start Flip Loop', icon='PLAY')

class DOPESHEET_OT_flip_loop_operator(bpy.types.Operator):
    bl_idname = 'dopesheet.flip_loop_operator'
    bl_label = 'Apply Flip Loop'
    bl_description = '1. Delete Right part of the animation,\n2. Paste Left part Flipped to Right,\n3. Duplicate First frame to Last'

    def execute(self, context):
        handle_flip_loop()
        return {'FINISHED'}

def handle_switch_to_nla_solo_action(obj):
    solo_nla_track = get_solo_nla_track(obj)
    if solo_nla_track:
        set_action_by_name(obj, solo_nla_track)

def get_solo_nla_track(obj):
    if obj.animation_data and obj.animation_data.nla_tracks:
        for track in obj.animation_data.nla_tracks:
            if track.is_solo:
                return track.name

def set_action_by_name(obj, action_name):
    if obj.animation_data:
        obj.animation_data.action = bpy.data.actions.get(action_name)

# class DOPESHEET_OT_toggle_flip_loop_operator(bpy.types.Operator):
#     bl_idname = 'dopesheet.toggle_flip_loop_operator'
#     bl_label = 'Toggle Flip Loop'
#     bl_description = 'While active: 1. deletes right part of the animation, 2. pastes left part flipped to right, 3. duplicates first frame to last'

#     def execute(self, context):
#         state = getState(bpy.context.scene)
#         state.flip_loop_active = not state.flip_loop_active
#         return {'FINISHED'}

def register():
    bpy.utils.register_class(DOPESHEET_PT_flip_loop_animation_panel)
    bpy.utils.register_class(DOPESHEET_OT_flip_loop_operator)
    # bpy.utils.register_class(DOPESHEET_OT_toggle_flip_loop_operator)
    bpy.utils.register_class(FlipLoopAnimationProperties)

    bpy.types.Scene.flip_loop_animation = bpy.props.PointerProperty(type=FlipLoopAnimationProperties)

    if depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)

def unregister():
    bpy.utils.unregister_class(DOPESHEET_PT_flip_loop_animation_panel)
    bpy.utils.unregister_class(DOPESHEET_OT_flip_loop_operator)
    # bpy.utils.unregister_class(DOPESHEET_OT_toggle_flip_loop_operator)
    bpy.utils.unregister_class(FlipLoopAnimationProperties)

    del bpy.types.Scene.flip_loop_animation

    if depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)

if __name__ == '__main__':
    register()
