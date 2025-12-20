# 抽取设置语言配置
extraction_settings = {
    "ZH_CN": {"title": {"name": "抽取设置", "description": "抽取功能设置"}},
    "EN_US": {"title": {"name": "Pick settings", "description": "Pick settings"}},
}

# 点名设置语言配置
roll_call_settings = {
    "ZH_CN": {
        "title": {"name": "点名设置", "description": "点名功能设置"},
        "extraction_function": {
            "name": "抽取功能",
            "description": "设置点名抽取功能",
        },
        "display_settings": {
            "name": "显示设置",
            "description": "设置点名结果显示方式",
        },
        "basic_animation_settings": {
            "name": "动画设置",
            "description": "设置点名动画效果",
        },
        "color_theme_settings": {
            "name": "颜色主题设置",
            "description": "设置点名结果颜色主题",
        },
        "student_image_settings": {
            "name": "学生头像设置",
            "description": "设置点名结果中学生头像显示",
        },
        "music_settings": {"name": "音乐设置", "description": "设置点名时播放的音乐"},
        "draw_mode": {
            "name": "抽取模式",
            "description": "设置点名抽取模式",
            "combo_items": ["重复抽取", "不重复抽取", "半重复抽取"],
        },
        "clear_record": {
            "name": "清除抽取记录方式",
            "description": "设置清除抽取记录的时机",
            "combo_items": ["重启后清除", "直到全部抽取完"],
            "combo_items_other": ["重启后清除", "直到全部抽取完", "无需清除"],
        },
        "half_repeat": {
            "name": "半重复抽取次数",
            "description": "设置每人被抽中多少次后清除抽取记录",
        },
        "draw_type": {
            "name": "抽取方式",
            "description": "设置点名抽取方式",
            "combo_items": ["随机抽取", "公平抽取"],
        },
        "default_class": {
            "name": "默认抽取名单",
            "description": "设置默认抽取名单",
        },
        "font_size": {"name": "字体大小", "description": "设置点名结果字体大小"},
        "display_format": {
            "name": "结果显示格式",
            "description": "设置点名结果显示格式",
            "combo_items": ["学号+姓名", "姓名", "学号"],
        },
        "show_random": {
            "name": "显示随机组员格式",
            "description": "设置随机组员显示格式",
            "combo_items": ["不显示", "组名[换行]姓名", "组名[短横杠]姓名"],
        },
        "animation": {
            "name": "动画模式",
            "description": "设置点名抽取动画效果",
            "combo_items": ["手动停止动画", "自动播放动画", "直接显示结果"],
        },
        "animation_interval": {
            "name": "动画间隔",
            "description": "设置点名动画间隔时间（毫秒）",
        },
        "autoplay_count": {
            "name": "自动播放次数",
            "description": "设置点名动画自动播放次数",
        },
        "animation_color_theme": {
            "name": "动画/结果颜色主题",
            "description": "设置点名动画/结果颜色主题",
            "combo_items": ["关闭", "随机颜色", "固定颜色"],
        },
        "animation_fixed_color": {
            "name": "动画/结果固定颜色",
            "description": "设置点名动画/结果固定颜色",
        },
        "student_image": {
            "name": "显示学生图片",
            "description": "设置是否显示学生图片",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "open_student_image_folder": {
            "name": "学生图片文件夹",
            "description": "管理学生图片文件，图片文件名需与学生姓名一致",
        },
    },
    "EN_US": {
        "title": {"name": "Picking settings", "description": "Picking settings"},
        "extraction_function": {
            "name": "Picking function",
            "description": "Set picking function",
        },
        "display_settings": {
            "name": "Display settings",
            "description": "Set the method to display the pick results",
        },
        "basic_animation_settings": {
            "name": "Animation settings",
            "description": "Set picking animations",
        },
        "color_theme_settings": {
            "name": "Color theme settings",
            "description": "Set the color theme of pick results",
        },
        "student_image_settings": {
            "name": "Student image settings",
            "description": "Set to show student avatars in the results",
        },
        "music_settings": {
            "name": "Music settings",
            "description": "Set the music to play on picking",
        },
        "draw_mode": {
            "name": "Picking mode",
            "description": "Set picking mode",
            "combo_items": {
                "0": "Pick with repeating",
                "1": "Pick without repeating",
                "2": "Semi-repeatedly pick",
            },
        },
        "clear_record": {
            "name": "Clear history method",
            "description": "Set the time to clean picking history",
            "combo_items": {"0": "Clear on restart", "1": "Until all have been picked"},
            "combo_items_other": {
                "0": "Clear on restart",
                "1": "Until all have been picked",
                "2": "Do not clear",
            },
        },
        "half_repeat": {
            "name": "Semi-repeated pick count",
            "description": "Set the maximum picked times of each person to clean history",
        },
        "draw_type": {
            "name": "Picking method",
            "description": "Set picking method",
            "combo_items": {"0": "Random pick", "1": "Fair pick"},
        },
        "font_size": {
            "name": "Font size",
            "description": "Set picking result font size",
        },
        "display_format": {
            "name": "Result display format",
            "description": "Set the results display format",
            "combo_items": {"0": "Student ID + Name", "1": "Name", "2": "Student ID"},
        },
        "show_random": {
            "name": "Format of showing random group member",
            "description": "Set random group member display format",
            "combo_items": {
                "0": "Hide",
                "1": "Group[New line]Name",
                "2": "Group name[Dash]name",
            },
        },
        "animation": {
            "name": "Animation mode",
            "description": "Set picking animations",
            "combo_items": {
                "0": "Manually stop animation",
                "1": "Automatically play animation",
                "2": "Directly show result",
            },
        },
        "animation_interval": {
            "name": "Animation interval",
            "description": "Set the interval between picking animations (ms)",
        },
        "autoplay_count": {
            "name": "Autoplay count",
            "description": "Set the number of times to animate",
        },
        "animation_color_theme": {
            "name": "Animation/Result Color Theme",
            "description": "Set the animate/result color theme",
            "combo_items": {"0": "Disabled", "1": "Random color", "2": "Fixed color"},
        },
        "animation_fixed_color": {
            "name": "Animation/Result fixed color",
            "description": "Set the animation/result color",
        },
        "student_image": {
            "name": "Show student images",
            "description": "Set whether to show student images",
        },
        "open_student_image_folder": {
            "name": "Student image folder",
            "description": "Manage student image files. Picture file names must match student name",
        },
    },
}

# 闪抽设置
quick_draw_settings = {
    "ZH_CN": {
        "title": {"name": "闪抽设置", "description": "闪抽功能设置"},
        "extraction_function": {
            "name": "抽取功能",
            "description": "设置闪抽抽取功能",
        },
        "display_settings": {
            "name": "显示设置",
            "description": "设置闪抽结果显示方式",
        },
        "basic_animation_settings": {
            "name": "动画设置",
            "description": "设置闪抽动画效果",
        },
        "color_theme_settings": {
            "name": "颜色主题设置",
            "description": "设置闪抽结果颜色主题",
        },
        "student_image_settings": {
            "name": "学生头像设置",
            "description": "设置闪抽结果中学生头像显示",
        },
        "music_settings": {"name": "音乐设置", "description": "设置闪抽时播放的音乐"},
        "draw_mode": {
            "name": "抽取模式",
            "description": "设置闪抽抽取模式",
            "combo_items": ["重复抽取", "不重复抽取", "半重复抽取"],
        },
        "clear_record": {
            "name": "清除抽取记录方式",
            "description": "设置清除闪抽抽取记录方式",
            "combo_items": ["重启后清除", "直到全部抽取完"],
            "combo_items_other": ["重启后清除", "直到全部抽取完", "无需清除"],
        },
        "half_repeat": {
            "name": "半重复抽取次数",
            "description": "设置每人被抽中多少次后清除抽取记录",
        },
        "draw_type": {
            "name": "抽取方式",
            "description": "设置闪抽抽取方式",
            "combo_items": ["随机抽取", "公平抽取"],
        },
        "default_class": {
            "name": "默认抽取名单",
            "description": "设置默认使用的抽取名单",
        },
        "font_size": {"name": "字体大小", "description": "设置闪抽结果字体大小"},
        "display_format": {
            "name": "结果显示格式",
            "description": "设置闪抽结果显示格式",
            "combo_items": ["学号+姓名", "姓名", "学号"],
        },
        "show_random": {
            "name": "显示随机组员格式",
            "description": "设置随机组员显示格式",
            "combo_items": ["不显示", "组名[换行]姓名", "组名[短横杠]姓名"],
        },
        "animation": {
            "name": "动画模式",
            "description": "设置闪抽抽取动画效果",
            "combo_items": ["自动播放动画", "直接显示结果"],
        },
        "animation_interval": {
            "name": "动画间隔",
            "description": "设置闪抽动画间隔时间(毫秒)",
        },
        "autoplay_count": {
            "name": "自动播放次数",
            "description": "设置闪抽动画自动播放次数",
        },
        "animation_color_theme": {
            "name": "动画/结果颜色主题",
            "description": "设置闪抽动画/结果颜色主题",
            "combo_items": ["关闭", "随机颜色", "固定颜色"],
        },
        "animation_fixed_color": {
            "name": "动画/结果固定颜色",
            "description": "设置闪抽动画/结果固定颜色",
        },
        "student_image": {
            "name": "显示学生图片",
            "description": "设置是否显示学生图片",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "open_student_image_folder": {
            "name": "学生图片文件夹",
            "description": "管理学生图片文件，图片文件名需与学生姓名一致",
        },
    },
    "EN_US": {
        "title": {"name": "Quick Pick settings", "description": "Quick Pick settings"},
        "extraction_function": {
            "name": "Picking function",
            "description": "Set Quick Pick function",
        },
        "display_settings": {
            "name": "Display settings",
            "description": "Set the method to display Quick Pick results",
        },
        "basic_animation_settings": {
            "name": "Animation settings",
            "description": "Set Quick Pick animations",
        },
        "color_theme_settings": {
            "name": "Color theme settings",
            "description": "Set the color theme of Quick Pick results",
        },
        "student_image_settings": {
            "name": "Student image settings",
            "description": "Set to show student avatars in the Quick Pick results",
        },
        "music_settings": {
            "name": "Music settings",
            "description": "Set the music to play when conducting Quick Pick",
        },
        "draw_mode": {
            "name": "Picking mode",
            "description": "Set Quick Pick mode",
            "combo_items": {
                "0": "Pick with repeating",
                "1": "Pick without repeating",
                "2": "Semi-repeatedly pick",
            },
        },
        "clear_record": {
            "name": "Clear history method",
            "description": "Set the method to clear Quick Pick records",
            "combo_items": {"0": "Clear on restart", "1": "Until all have been picked"},
            "combo_items_other": {
                "0": "Clear on restart",
                "1": "Until all have been picked",
                "2": "Do not clear",
            },
        },
        "half_repeat": {
            "name": "Semi-repeated pick count",
            "description": "Set the maximum picked times of each person to clean history",
        },
        "draw_type": {
            "name": "Picking method",
            "description": "Set Quick Pick method",
            "combo_items": {"0": "Random pick", "1": "Fair pick"},
        },
        "default_class": {
            "name": "Default picking list",
            "description": "Set the default list used for extraction",
        },
        "font_size": {
            "name": "Font size",
            "description": "Set Quick Pick result font size",
        },
        "display_format": {
            "name": "Result display format",
            "description": "Set Quick Pick display format",
            "combo_items": {"0": "Student ID + Name", "1": "Name", "2": "Student ID"},
        },
        "show_random": {
            "name": "Format of showing random group member",
            "description": "Set random group member display format",
            "combo_items": {
                "0": "Hide",
                "1": "Group[New line]Name",
                "2": "Group name[Dash]name",
            },
        },
        "animation": {
            "name": "Animation mode",
            "description": "Set Quick Pick animations",
            "combo_items": {
                "0": "Manually stop animation",
                "1": "Automatically play animation",
                "2": "Directly show result",
            },
        },
        "animation_interval": {
            "name": "Animation interval",
            "description": "Set the interval between Quick Pick (ms)",
        },
        "autoplay_count": {
            "name": "Autoplay count",
            "description": "Configure Quick Pick animation autoplay count",
        },
        "animation_color_theme": {
            "name": "Animation color theme",
            "description": "Set the animate/result color theme of Quick Pick",
            "combo_items": {"0": "Disabled", "1": "Random color", "2": "Fixed color"},
        },
        "result_color_theme": {
            "name": "Results color theme",
            "description": "Set the color theme of Quick Pick results",
            "combo_items": {"0": "Disabled", "1": "Random color", "2": "Fixed color"},
        },
        "animation_fixed_color": {
            "name": "Animation fixed color",
            "description": "Set the animation/result color of Quick Pick",
        },
        "result_fixed_color": {
            "name": "Results fixed color",
            "description": "Configure fixed color for Quick Pick result display",
        },
        "student_image": {
            "name": "Show student images",
            "description": "Set whether to show student images",
        },
        "open_student_image_folder": {
            "name": "Student image folder",
            "description": "Manage student image files. Picture file names must match student name",
        },
    },
}

# 即抽设置
instant_draw_settings = {
    "ZH_CN": {
        "title": {"name": "即抽设置", "description": "即抽功能设置"},
        "extraction_function": {
            "name": "抽取功能",
            "description": "设置即抽抽取功能",
        },
        "display_settings": {
            "name": "显示设置",
            "description": "设置即抽结果显示方式",
        },
        "basic_animation_settings": {
            "name": "动画设置",
            "description": "设置即抽动画效果",
        },
        "color_theme_settings": {
            "name": "颜色主题设置",
            "description": "设置即抽结果颜色主题",
        },
        "student_image_settings": {
            "name": "学生头像设置",
            "description": "设置即抽结果中学生头像显示",
        },
        "music_settings": {"name": "音乐设置", "description": "设置即抽时播放的音乐"},
        "draw_mode": {
            "name": "抽取模式",
            "description": "设置即抽抽取模式",
            "combo_items": ["重复抽取", "不重复抽取", "半重复抽取"],
        },
        "clear_record": {
            "name": "清除抽取记录方式",
            "description": "设置清除即抽抽取记录方式",
            "combo_items": ["重启后清除", "直到全部抽取完"],
            "combo_items_other": ["重启后清除", "直到全部抽取完", "无需清除"],
        },
        "half_repeat": {
            "name": "半重复抽取次数",
            "description": "设置每人被抽中多少次后清除抽取记录",
        },
        "draw_type": {
            "name": "抽取方式",
            "description": "设置即抽抽取方式",
            "combo_items": ["随机抽取", "公平抽取"],
        },
        "default_class": {
            "name": "默认抽取名单",
            "description": "设置默认使用的抽取名单",
        },
        "font_size": {"name": "字体大小", "description": "设置即抽结果字体大小"},
        "display_format": {
            "name": "结果显示格式",
            "description": "设置即抽结果显示格式",
            "combo_items": ["学号+姓名", "姓名", "学号"],
        },
        "show_random": {
            "name": "显示随机组员格式",
            "description": "设置随机组员显示格式",
            "combo_items": ["不显示", "组名[换行]姓名", "组名[短横杠]姓名"],
        },
        "animation": {
            "name": "动画模式",
            "description": "设置即抽抽取动画效果",
            "combo_items": ["自动播放动画", "直接显示结果"],
        },
        "animation_interval": {
            "name": "动画间隔",
            "description": "设置即抽动画间隔时间(毫秒)",
        },
        "autoplay_count": {
            "name": "自动播放次数",
            "description": "设置即抽动画自动播放次数",
        },
        "animation_color_theme": {
            "name": "动画/结果颜色主题",
            "description": "设置即抽动画/结果颜色主题",
            "combo_items": ["关闭", "随机颜色", "固定颜色"],
        },
        "animation_fixed_color": {
            "name": "动画/结果固定颜色",
            "description": "设置即抽动画/结果固定颜色",
        },
        "student_image": {
            "name": "显示学生图片",
            "description": "设置是否显示学生图片",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "open_student_image_folder": {
            "name": "学生图片文件夹",
            "description": "管理学生图片文件，图片文件名需与学生姓名一致",
        },
    },
    "EN_US": {
        "title": {
            "name": "Instant Pick settings",
            "description": "Instant Pick settings",
        },
        "extraction_function": {
            "name": "Picking function",
            "description": "Set Instant Pick function",
        },
        "display_settings": {
            "name": "Display settings",
            "description": "Set the method to display the Instant Pick results",
        },
        "basic_animation_settings": {
            "name": "Animation settings",
            "description": "Set Instant Pick animations",
        },
        "color_theme_settings": {
            "name": "Color theme settings",
            "description": "Set the color theme of Instant Pick results",
        },
        "student_image_settings": {
            "name": "Student image settings",
            "description": "Set to show student avatars in the Instant Pick results",
        },
        "music_settings": {
            "name": "Music settings",
            "description": "Set the music to play when conducting Instant Puck",
        },
        "draw_mode": {
            "name": "Picking mode",
            "description": "Set Instant Pick mode",
            "combo_items": {
                "0": "Pick with repeating",
                "1": "Pick without repeating",
                "2": "Semi-repeatedly pick",
            },
        },
        "clear_record": {
            "name": "Clear history method",
            "description": "Sets the method to clear Instant Pick history",
            "combo_items": {"0": "Clear on restart", "1": "Until all have been picked"},
            "combo_items_other": {
                "0": "Clear on restart",
                "1": "Until all have been picked",
                "2": "Do not clear",
            },
        },
        "half_repeat": {
            "name": "Semi-repeated pick count",
            "description": "Set how many times each is picked and clear the history",
        },
        "draw_type": {
            "name": "Picking method",
            "description": "Set Instant Pick method",
            "combo_items": {"0": "Random pick", "1": "Fair pick"},
        },
        "default_class": {
            "name": "Default picking list",
            "description": "Set the default list used for extraction",
        },
        "font_size": {
            "name": "Font size",
            "description": "Set the Instant Pick result font size",
        },
        "display_format": {
            "name": "Result display format",
            "description": "Set the Instant Pick display format",
            "combo_items": {"0": "Student ID + Name", "1": "Name", "2": "Student ID"},
        },
        "show_random": {
            "name": "Format of showing random group member",
            "description": "Set random group member display format",
            "combo_items": {
                "0": "Hide",
                "1": "Group[New line]Name",
                "2": "Group name[Dash]name",
            },
        },
        "animation": {
            "name": "Animation mode",
            "description": "Set Instant Pick animations",
            "combo_items": {
                "0": "Manually stop animation",
                "1": "Automatically play animation",
                "2": "Directly show result",
            },
        },
        "animation_interval": {
            "name": "Animation interval",
            "description": "Set Instant Picking animation interval (ms)",
        },
        "autoplay_count": {
            "name": "Autoplay count",
            "description": "Configure Instant Pick animation autoplay count",
        },
        "animation_color_theme": {
            "name": "Animation color theme",
            "description": "Set Instant Pick animate/result color theme",
            "combo_items": {"0": "Disabled", "1": "Random color", "2": "Fixed color"},
        },
        "result_color_theme": {
            "name": "Results color theme",
            "description": "Set Instant Pick result color theme",
            "combo_items": {"0": "Disabled", "1": "Random color", "2": "Fixed color"},
        },
        "animation_fixed_color": {
            "name": "Animation fixed color",
            "description": "Set Instant Pick animation/result fixed color",
        },
        "result_fixed_color": {
            "name": "Results fixed color",
            "description": "Set Instant Pick result fixed color",
        },
        "student_image": {
            "name": "Show student images",
            "description": "Set whether to show student images",
        },
        "open_student_image_folder": {
            "name": "Student image folder",
            "description": "Manage student image files. Picture file names must match student name",
        },
    },
}

# 抽奖设置
lottery_settings = {
    "ZH_CN": {
        "title": {"name": "抽奖设置", "description": "抽奖功能设置"},
        "extraction_function": {
            "name": "抽取功能",
            "description": "设置抽奖抽取功能",
        },
        "display_settings": {
            "name": "显示设置",
            "description": "设置抽奖结果显示方式",
        },
        "basic_animation_settings": {
            "name": "动画设置",
            "description": "设置抽奖动画效果",
        },
        "color_theme_settings": {
            "name": "颜色主题设置",
            "description": "设置抽奖结果颜色主题",
        },
        "lottery_image_settings": {
            "name": "奖品图片设置",
            "description": "设置抽奖结果中奖品图片显示",
        },
        "music_settings": {"name": "音乐设置", "description": "设置抽奖时播放的音乐"},
        "draw_mode": {
            "name": "抽取模式",
            "description": "设置抽奖抽取模式",
            "combo_items": ["重复抽取", "不重复抽取", "半重复抽取"],
        },
        "clear_record": {
            "name": "清除抽取记录方式",
            "description": "设置清除抽奖抽取记录方式",
            "combo_items": ["重启后清除", "直到全部抽取完"],
            "combo_items_other": ["重启后清除", "直到全部抽取完", "无需清除"],
        },
        "half_repeat": {
            "name": "半重复抽取次数",
            "description": "设置每人被抽中多少次后清除抽取记录",
        },
        "draw_type": {
            "name": "抽取方式",
            "description": "设置抽奖抽取方式",
            "combo_items": ["随机抽取", "公平抽取"],
        },
        "default_pool": {
            "name": "默认抽取名单",
            "description": "设置默认使用的抽取名单",
        },
        "font_size": {"name": "字体大小", "description": "设置抽奖结果字体大小"},
        "display_format": {
            "name": "结果显示格式",
            "description": "设置抽奖结果显示格式",
            "combo_items": ["序号+名称", "名称", "序号"],
        },
        "animation": {
            "name": "动画模式",
            "description": "设置抽奖抽取动画效果",
            "combo_items": ["手动停止动画", "自动播放动画", "直接显示结果"],
        },
        "animation_interval": {
            "name": "动画间隔",
            "description": "设置抽奖动画间隔时间(毫秒)",
        },
        "autoplay_count": {
            "name": "自动播放次数",
            "description": "设置抽奖动画自动播放次数",
        },
        "animation_color_theme": {
            "name": "动画/结果颜色主题",
            "description": "设置抽奖动画/结果颜色主题",
            "combo_items": ["关闭", "随机颜色", "固定颜色"],
        },
        "animation_fixed_color": {
            "name": "动画/结果固定颜色",
            "description": "设置抽奖动画/结果固定颜色",
        },
        "lottery_image": {
            "name": "显示奖品图片",
            "description": "设置是否显示奖品图片",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "open_lottery_image_folder": {
            "name": "奖品图片文件夹",
            "description": "管理奖品图片文件，图片文件名需与奖品名称一致",
        },
    },
    "EN_US": {
        "title": {"name": "Lottery settings", "description": "Lottery settings"},
        "extraction_function": {
            "name": "Picking function",
            "description": "Set lottery function",
        },
        "display_settings": {
            "name": "Display settings",
            "description": "Set the method to display the lottery results",
        },
        "basic_animation_settings": {
            "name": "Animation settings",
            "description": "Set lottery animations",
        },
        "color_theme_settings": {
            "name": "Color theme settings",
            "description": "Set the color theme of lottery results",
        },
        "student_image_settings": {
            "name": "Prize image settings",
            "description": "Set the prize image to display in lottery results",
        },
        "music_settings": {
            "name": "Music settings",
            "description": "Set the music to play when lottery",
        },
        "draw_mode": {
            "name": "Picking mode",
            "description": "Set lottery mode",
            "combo_items": {
                "0": "Pick with repeating",
                "1": "Pick without repeating",
                "2": "Semi-repeatedly pick",
            },
        },
        "clear_record": {
            "name": "Clear history method",
            "description": "Sets the method to clear lottery records",
            "combo_items": {"0": "Clear on restart", "1": "Until all have been picked"},
            "combo_items_other": {
                "0": "Clear on restart",
                "1": "Until all have been picked",
                "2": "Do not clear",
            },
        },
        "half_repeat": {
            "name": "Semi-repeated pick count",
            "description": "Set the maximum picked times of each person to clean history",
        },
        "draw_type": {
            "name": "Picking method",
            "description": "Set lottery function",
            "combo_items": {"0": "Random pick", "1": "Fair pick"},
        },
        "font_size": {
            "name": "Font size",
            "description": "Set the lottery result font size",
        },
        "display_format": {
            "name": "Result display format",
            "description": "Set the lottery results display format",
            "combo_items": {"0": "Serial + Name", "1": "Name", "2": "Serial"},
        },
        "animation": {
            "name": "Animation mode",
            "description": "Set lottery animations",
            "combo_items": {
                "0": "Manually stop animation",
                "1": "Automatically play animation",
                "2": "Directly show result (no animation)",
            },
        },
        "animation_interval": {
            "name": "Animation interval",
            "description": "Set the interval between lottery animations (ms)",
        },
        "autoplay_count": {
            "name": "Autoplay count",
            "description": "Set the number of times to animate",
        },
        "animation_color_theme": {
            "name": "Animation color theme",
            "description": "Set the animate/result color theme",
            "combo_items": {"0": "Disabled", "1": "Theme color", "2": "Fixed color"},
        },
        "result_color_theme": {
            "name": "Results color theme",
            "description": "Set the color theme of lottery results",
            "combo_items": {"0": "Disabled", "1": "Random color", "2": "Fixed color"},
        },
        "animation_fixed_color": {
            "name": "Animation fixed color",
            "description": "Set the animation/result color",
        },
        "result_fixed_color": {
            "name": "Results fixed color",
            "description": "Configure fixed color for lottery result display",
        },
        "lottery_image": {
            "name": "Show prize images",
            "description": "Set whether to show prize images",
        },
        "open_lottery_image_folder": {
            "name": "Prize image folder",
            "description": "Manage s\nprize image files. Picture file names must match prize names",
        },
        "lottery_image_settings": {
            "name": "Prize image settings",
            "description": "Set the prize image to display in lottery results",
        },
    },
}
