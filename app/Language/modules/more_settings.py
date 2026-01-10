# 更多设置语言配置
more_settings = {
    "ZH_CN": {
        "title": {"name": "更多设置", "description": "更多功能设置"},
    },
    "EN_US": {"title": {"name": "More settings", "description": "More settings"}},
}

settings = {
    "ZH_CN": {
        "title": {"name": "设置", "description": "设置窗口"},
    },
    "EN_US": {"title": {"name": "Settings", "description": "Settings window"}},
}

# 课程相关语言配置
course_settings = {
    "ZH_CN": {
        "title": {"name": "课程相关", "description": "设置课间禁用和课程表导入"},
        "class_break_settings": {
            "name": "课间禁用设置",
            "description": "设置课间禁用功能",
        },
        "cses_import_settings": {
            "name": "CSES课程表导入",
            "description": "从CSES格式文件导入课程表",
        },
        "class_break_function": {
            "name": "课间禁用功能",
            "description": "开启后，在下课时间段内抽取需要安全验证",
        },
        "pre_class_enable_time": {
            "name": "上课前提前解禁时间",
            "description": "在上课前多少秒提前解禁（0-1440秒）",
        },
        "cses_import": {
            "name": "课程表导入",
            "description": "从CSES格式文件导入上课时间段，用于课间禁用功能",
        },
        "verification_function": {
            "name": "验证流程功能",
            "description": "启用后，在非上课时段触发时将弹出安全验证；若关闭则直接禁用控件",
        },
        "pre_class_reset_settings": {
            "name": "课前重置设置",
            "description": "设置课前重置临时记录功能",
        },
        "pre_class_reset_function": {
            "name": "课前重置功能",
            "description": "启用后，在上课前指定秒数内自动清除临时记录和界面结果",
        },
        "pre_class_reset_time": {
            "name": "课前重置时间",
            "description": "在上课前多少秒清除临时记录和界面结果（1-1440秒）",
        },
        "import_from_file": {"name": "从文件导入"},
        "importing": {"name": "导入中..."},
        "view_current_config": {"name": "查看当前配置"},
        "no_schedule_imported": {"name": "未导入课程表"},
        "schedule_imported": {"name": "已导入 {} 个上课时间段"},
        "copy_to_clipboard": {"name": "复制到剪贴板"},
        "save_as_file": {"name": "保存为文件"},
        "copy_success": {"name": "复制成功"},
        "template_copied": {"name": "模板已复制到剪贴板"},
        "save_success": {"name": "保存成功"},
        "template_saved": {"name": "模板已保存到: {}"},
        "import_success": {"name": "成功导入课程表: {}"},
        "import_failed": {"name": "导入失败: {}"},
        "import_error": {"name": "导入过程中发生错误: {}"},
        "template_title": {"name": "CSES课程表模板"},
        "select_cses_file": {"name": "选择CSES课程表文件"},
        "yaml_files": {"name": "YAML文件 (*.yaml *.yml)"},
        "all_files": {"name": "所有文件 (*.*)"},
        "save_template": {"name": "保存CSES模板"},
        "cses_template": {"name": "cses_template.yaml"},
        "save_failed": {"name": "保存失败: {}"},
        "copy_failed": {"name": "复制失败: {}"},
        "cses_file_format_error": {"name": "CSES文件格式错误或文件无法读取"},
        "cses_content_format_error": {"name": "CSES内容格式错误"},
        "no_valid_time_periods": {"name": "未能从课程表中提取有效的时间段信息"},
        "save_settings_failed": {"name": "保存设置失败"},
        "no_cses_folder": {"name": "未找到CSES文件夹"},
        "no_schedule_file": {"name": "未导入课程表文件"},
        "unknown": {"name": "未知"},
        "unknown_course": {"name": "未知课程"},
        "parse_failed": {"name": "解析失败"},
        "load_config_failed": {"name": "加载配置失败: {}"},
        "table_headers": {"name": ["星期", "课程名称", "开始时间", "结束时间", "老师"]},
        "day_map": {
            "1": "周一",
            "2": "周二",
            "3": "周三",
            "4": "周四",
            "5": "周五",
            "6": "周六",
            "7": "周日",
        },
        "subject_history_filter_settings": {
            "name": "科目历史记录过滤",
            "description": "设置科目历史记录过滤功能",
        },
        "subject_history_filter_function": {
            "name": "科目历史记录过滤",
            "description": "启用后，计算权重时只使用当前科目的历史记录",
        },
        "data_source_settings": {
            "name": "数据源选择",
            "description": "设置课程数据源",
        },
        "data_source_function": {
            "name": "数据源选择",
            "description": "选择课程数据的来源",
            "combo_items": [
                "不使用数据源",
                "使用CSES课表数据",
                "使用ClassIsland数据源",
            ],
        },
    },
    "EN_US": {
        "title": {"name": "Course Related", "description": "设置课间禁用和课程表导入"},
        "class_break_settings": {
            "name": "课间禁用设置",
            "description": "设置课间禁用功能",
        },
        "cses_import_settings": {
            "name": "CSES Schedule Importation",
            "description": "Import schedule from CSES file",
        },
        "class_break_function": {
            "name": "Disable draw during class break",
            "description": "Draw during class breaks need security authorization when enabled",
        },
        "pre_class_enable_time": {
            "name": "Pre-class enable time",
            "description": "How many seconds before class to enable (0-1440 seconds)",
        },
        "cses_import": {
            "name": "Schedule import",
            "description": "Import class timetable from CSES file for auto-disable during class breaks",
        },
        "import_from_file": {"name": "Import from file"},
        "importing": {"name": "导入中..."},
        "view_template": {"name": "View template"},
        "no_schedule_imported": {"name": "Haven't imported schedule yet"},
        "copy_to_clipboard": {"name": "复制到剪贴板"},
        "save_as_file": {"name": "保存为文件"},
        "close": {"name": "Disabled"},
        "copy_success": {"name": "复制成功"},
        "template_copied": {"name": "Template has been copied to clipboard"},
        "save_success": {"name": "Item successfully saved"},
        "template_saved": {"name": "Template have been saved to: {}"},
        "import_error": {"name": "Error {} occurred when importing"},
        "template_title": {"name": "CSES schedule template"},
        "select_cses_file": {"name": "选择CSES课程表文件"},
        "yaml_files": {"name": "YAML文件 (*.yaml *.yml)"},
        "all_files": {"name": "所有文件 (*.*)"},
        "save_template": {"name": "保存CSES模板"},
        "cses_template": {"name": "cses_template.yaml"},
        "verification_function": {
            "name": "验证流程功能",
            "description": "启用后，在非上课时段触发时将弹出安全验证；若关闭则直接禁用控件",
        },
        "pre_class_reset_settings": {
            "name": "Pre-class reset settings",
            "description": "Settings for pre-class reset of temporary records",
        },
        "pre_class_reset_function": {
            "name": "Pre-class reset function",
            "description": "When enabled, automatically clear temporary records and interface results within specified seconds before class",
        },
        "pre_class_reset_time": {
            "name": "Pre-class reset time",
            "description": "How many seconds before class to clear temporary records and interface results (1-1440 seconds)",
        },
        "view_current_config": {"name": "查看当前配置"},
        "schedule_imported": {"name": "已导入 {} 个上课时间段"},
        "import_success": {"name": "成功导入课程表: {}"},
        "import_failed": {"name": "导入失败: {}"},
        "save_failed": {"name": "保存失败: {}"},
        "copy_failed": {"name": "复制失败: {}"},
        "cses_file_format_error": {"name": "CSES文件格式错误或文件无法读取"},
        "cses_content_format_error": {"name": "CSES内容格式错误"},
        "no_valid_time_periods": {"name": "未能从课程表中提取有效的时间段信息"},
        "save_settings_failed": {"name": "保存设置失败"},
        "no_cses_folder": {"name": "未找到CSES文件夹"},
        "no_schedule_file": {"name": "未导入课程表文件"},
        "unknown": {"name": "未知"},
        "unknown_course": {"name": "未知课程"},
        "parse_failed": {"name": "解析失败"},
        "load_config_failed": {"name": "加载配置失败: {}"},
        "table_headers": {
            "name": {
                "0": "星期",
                "1": "课程名称",
                "2": "开始时间",
                "3": "结束时间",
                "4": "老师",
            }
        },
        "day_map": {
            "1": "周一",
            "2": "周二",
            "3": "周三",
            "4": "周四",
            "5": "周五",
            "6": "周六",
            "7": "周日",
        },
        "subject_history_filter_settings": {
            "name": "Subject History Filter",
            "description": "Settings for subject history record filtering",
        },
        "subject_history_filter_function": {
            "name": "Subject History Filter",
            "description": "When enabled, only use current subject's history records for weight calculation",
        },
        "data_source_settings": {
            "name": "Data Source Selection",
            "description": "Settings for course data source",
        },
        "data_source_function": {
            "name": "Data Source Selection",
            "description": "Select the source of course data",
            "combo_items": ["No Data Source", "Use CSES Schedule", "Use ClassIsland"],
        },
    },
}

# 快捷键设置
shortcut_settings = {
    "ZH_CN": {
        "title": {"name": "快捷键设置", "description": "设置快捷键功能"},
        "function": {"name": "功能"},
        "shortcut": {"name": "快捷键"},
        "press_shortcut": {"name": "点击此处设置快捷键"},
        "enable_shortcut": {
            "name": "启用快捷键",
            "description": "启用后可使用快捷键快速操作",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "open_roll_call_page": {"name": "打开点名页面"},
        "use_quick_draw": {"name": "使用闪抽"},
        "open_lottery_page": {"name": "打开抽奖页面"},
        "increase_roll_call_count": {"name": "增加点名人数"},
        "decrease_roll_call_count": {"name": "减少点名人数"},
        "increase_lottery_count": {"name": "增加抽奖人数"},
        "decrease_lottery_count": {"name": "减少抽奖人数"},
        "start_roll_call": {"name": "开始点名"},
        "start_lottery": {"name": "开始抽奖"},
    },
    "EN_US": {
        "title": {"name": "Shortcut settings", "description": "Shortcut settings"},
        "function": {"name": "Function"},
        "shortcut": {"name": "Shortcut"},
        "press_shortcut": {"name": "Click here to set shortcut"},
        "enable_shortcut": {
            "name": "Enable shortcut",
            "description": "Enable shortcuts for quick operations",
            "switchbutton_name": {"enable": "Enable", "disable": "Disable"},
        },
        "open_roll_call_page": {"name": "Open roll call page"},
        "use_quick_draw": {"name": "Use quick draw"},
        "open_lottery_page": {"name": "Open lottery page"},
        "increase_roll_call_count": {"name": "Increase roll call count"},
        "decrease_roll_call_count": {"name": "Decrease roll call count"},
        "increase_lottery_count": {"name": "Increase lottery count"},
        "decrease_lottery_count": {"name": "Decrease lottery count"},
        "start_roll_call": {"name": "Start roll call"},
        "start_lottery": {"name": "Start lottery"},
    },
}

# 关于语言配置
about = {
    "ZH_CN": {
        "title": {"name": "关于", "description": "软件关于页面信息"},
        "github": {"name": "Github", "description": "访问项目代码仓库"},
        "bilibili": {
            "name": "Bilibili",
            "description": "访问黎泽懿_Aionflux的Bilibili账号",
        },
        "contributor": {
            "name": "贡献人员",
            "description": "点击查看详细贡献者信息",
            "contributor_role_1": "设计、创意、策划\n维护、文档、测试",
            "contributor_role_2": "维护",
            "contributor_role_3": "响应式前端页面\n设计及维护、文档",
            "contributor_role_4": "创意、文档",
            "contributor_role_5": "创意、维护",
            "contributor_role_6": "应用测试、文档、安装包制作",
            "contributor_role_7": "响应式前端页面\n设计及维护、文档",
            "contributor_role_10": "ClassIsland 插件\nClassIsland 联动",
        },
        "donation": {"name": "捐赠支持", "description": "支持项目发展，感谢您的捐赠"},
        "website": {"name": "SecRandom 官网", "description": "访问SecRandom软件官网"},
        "copyright": {"name": "版权", "description": "SecRandom遵循GPL-3.0协议"},
        "version": {"name": "版本", "description": "显示当前软件版本号"},
    },
    "EN_US": {
        "title": {"name": "About", "description": "APP about page"},
        "github": {"name": "GitHub", "description": "Visit project repository"},
        "bilibili": {
            "name": "Bilibili",
            "description": "Visit 黎泽懿_Aionflux's Bilibili account",
        },
        "contributor": {
            "name": "Contributors",
            "description": "Click to show full contributor information",
            "contributor_role_1": "Design & Creativity & Test &\nMaintenance & Documentation",
            "contributor_role_2": "Maintenance",
            "contributor_role_3": "Responsive frontend page Design and Maintenance & Documentation",
            "contributor_role_4": "Creativity & Documentation",
            "contributor_role_5": "Creativity & Maintenance",
            "contributor_role_6": "Test & Documentation & Install Package Making",
            "contributor_role_7": "Responsive frontend page Design and Maintenance & Documentation",
            "contributor_role_10": "Test & Documentation & Install Package Making",
        },
        "donation": {"name": "Donate", "description": "Buy me a coffee"},
        "check_update": {
            "name": "Check for updates",
            "description": "Check for updates",
        },
        "website": {
            "name": "SecRandom Website",
            "description": "Visit SecRandom's official website",
        },
        "channel": {
            "name": "Update channel",
            "description": "Select SecRandom software update channel",
            "combo_items": {"0": "Official version", "1": "Beta version"},
        },
        "copyright": {"name": "Copyright", "description": "SecRandom follows GPL-3.0"},
        "version": {"name": "Version", "description": "Show current version"},
    },
}

# 内幕设置语言配置
behind_scenes_settings = {
    "ZH_CN": {
        "title": {"name": "内幕设置", "description": "设置特定人员的抽取概率"},
        "select_mode": {"name": "选择模式", "description": "选择点名或抽奖模式"},
        "mode_options": {"combo_items": ["点名", "抽奖"]},
        "select_list": {"name": "选择名单", "description": "选择要设置概率的名单"},
        "select_class_name": {
            "name": "选择班级",
            "description": "选择要设置概率的班级",
        },
        "select_pool_name": {"name": "选择奖池", "description": "选择要设置概率的奖池"},
        "enabled": {"name": "启用", "description": "是否启用该人员的概率设置"},
        "id": {"name": "学号", "description": "学生学号"},
        "name": {"name": "姓名", "description": "学生姓名"},
        "prize": {"name": "奖品", "description": "关联的奖品（抽奖模式）"},
        "probability": {
            "name": "权重",
            "description": "抽取权重（0=禁用，1.0=正常，≥1000=必中）",
        },
    },
    "EN_US": {
        "title": {
            "name": "Behind the Scenes Settings",
            "description": "Set draw probability for specific persons",
        },
        "select_mode": {
            "name": "Select Mode",
            "description": "Select roll call or lottery mode",
        },
        "mode_options": {"combo_items": ["Roll Call", "Lottery"]},
        "select_list": {
            "name": "Select List",
            "description": "Select list to set probability",
        },
        "select_class_name": {
            "name": "Select Class",
            "description": "Select the class to set probability",
        },
        "select_pool_name": {
            "name": "Select Pool",
            "description": "Select to pool set probability",
        },
        "enabled": {
            "name": "Enabled",
            "description": "Whether to enable probability settings for this person",
        },
        "id": {"name": "ID", "description": "Student ID"},
        "name": {"name": "Name", "description": "Student name"},
        "prize": {"name": "Prize", "description": "Associated prize (lottery mode)"},
        "probability": {
            "name": "Weight",
            "description": "Draw weight (0=Disabled, 1.0=Normal, ≥1000=Guaranteed)",
        },
    },
}

# 翻译文件信息
translate_JSON_file = {
    "ZH_CN": {
        "name": "简体中文",
        "translated_personnel": "lzy98276",
    },
    "EN_US": {
        "name": "English",
        "translated_personnel": "",
    },
}
