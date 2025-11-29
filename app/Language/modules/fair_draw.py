# 公平抽取设置语言配置
fair_draw_settings = {
    "ZH_CN": {
        "title": {"name": "公平抽取设置", "description": "公平抽取功能设置"},
        "fair_draw_set": {
            "name": "公平抽取",
            "description": "配置公平抽取算法相关设置",
        },
        "basic_fair_settings": {
            "name": "基础公平设置",
            "description": "配置公平抽取的基础计算方式",
        },
        "weight_range_settings": {
            "name": "权重范围设置",
            "description": "配置权重的基础值和范围",
        },
        "shield_settings": {
            "name": "抽取后屏蔽设置",
            "description": "配置抽取后的屏蔽规则",
        },
        "frequency_settings": {
            "name": "频率函数设置",
            "description": "配置频率惩罚的计算方式",
        },
        "balance_weight_settings": {
            "name": "平衡权重设置",
            "description": "配置各平衡因子的权重占比",
        },
        "cold_start_settings": {
            "name": "冷启动设置",
            "description": "配置新班级初始阶段的冷启动规则",
        },
        "fair_draw": {
            "name": "按总抽取次数公平抽取",
            "description": "启用后根据总抽取次数进行公平抽取",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "fair_draw_group": {
            "name": "按组公平抽取",
            "description": "启用后按组参与公平抽取计算",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "fair_draw_gender": {
            "name": "按性别公平抽取",
            "description": "启用后按性别参与公平抽取计算",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "fair_draw_time": {
            "name": "按时间公平抽取",
            "description": "启用后按时间参与公平抽取计算",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "base_weight": {"name": "基础权重", "description": "设置每个选项的基础权重值"},
        "min_weight": {
            "name": "权重范围最小值",
            "description": "设置每个选项权重最小值",
        },
        "max_weight": {
            "name": "权重范围最大值",
            "description": "设置每个选项权重最大值",
        },
        "frequency_function": {
            "name": "频率惩罚函数",
            "description": "选择频率惩罚的计算函数类型",
            "combo_items": ["线性", "平方根", "指数"],
        },
        "frequency_weight": {
            "name": "频率惩罚权重",
            "description": "调整频率惩罚在总权重中的占比",
        },
        "group_weight": {
            "name": "小组平衡权重",
            "description": "调整小组平衡在总权重中的占比",
        },
        "gender_weight": {
            "name": "性别平衡权重",
            "description": "调整性别平衡在总权重中的占比",
        },
        "time_weight": {
            "name": "时间因子权重",
            "description": "调整时间因子在总权重中的占比",
        },
        "cold_start_enabled": {
            "name": "启用冷启动模式",
            "description": "新班级或初始阶段使用冷启动模式",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "cold_start_rounds": {
            "name": "冷启动轮次",
            "description": "设置冷启动模式的轮次数量",
        },
        "shield_enabled": {
            "name": "启用抽取后屏蔽",
            "description": "启用后，抽取的学生在指定时间内不会被重复抽取",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "shield_time": {
            "name": "屏蔽时间",
            "description": "设置抽取后屏蔽的时间长度",
        },
        "shield_time_unit": {
            "name": "屏蔽时间单位",
            "description": "选择屏蔽时间的时间单位",
            "combo_items": ["秒", "分钟", "小时"],
        },
    }
}
