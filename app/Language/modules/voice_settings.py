# 语音设置语言配置
voice_settings = {
    "ZH_CN": {"title": {"name": "语音设置", "description": "配置语音播报相关功能"}}
}

# 基础语音设置语言配置
basic_voice_settings = {
    "ZH_CN": {
        "title": {"name": "基础语音设置", "description": "配置基础语音播报功能"},
        "voice_engine_group": {
            "name": "语音引擎",
            "description": "选择语音合成引擎类型",
        },
        "volume_group": {"name": "语音设置", "description": "调整语音播报相关设置"},
        "voice_enable": {
            "name": "语音功能开关",
            "description": "开启或关闭语音播报功能",
            "switchbutton_name": {"enable": "开启", "disable": "关闭"},
        },
        "voice_engine": {
            "name": "语音引擎",
            "description": "选择语音合成引擎类型",
            "combo_items": ["系统TTS", "Edge TTS"],
        },
        "edge_tts_voice_name": {
            "name": "Edge TTS 语音角色",
            "description": "选择Edge TTS的语音播报角色",
            "combo_items": [
                "zh-CN-XiaoxiaoNeural",
                "zh-CN-YunxiNeural",
                "zh-CN-XiaoyiNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
            ],
        },
        "volume_size": {"name": "播报音量", "description": "调整语音播报的音量大小"},
        "speech_rate": {"name": "语速调节", "description": "调整语音播报的语速"},
        "system_volume_control": {
            "name": "系统音量控制",
            "description": "是否开启系统音量自动控制",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "system_volume_size": {
            "name": "系统音量大小",
            "description": "设置系统音量的大小",
        },
    },
    "EN_US": {
        "title": {
            "name": "Basic voice settings",
            "description": "配置基础语音播报功能",
        },
        "voice_engine_group": {
            "name": "Voice engine",
            "description": "选择语音合成引擎类型",
        },
        "volume_group": {
            "name": "Volume settings",
            "description": "调整语音播报音量大小",
        },
        "voice_enable": {
            "name": "Voice Function Switch",
            "description": "Turn the voice broadcast function on or off",
            "switchbutton_name": {"enable": "ON", "disable": "OFF"},
        },
        "system_volume_group": {
            "name": "System volume control",
            "description": "选择要控制的系统音量类型",
        },
        "voice_engine": {
            "name": "Voice engine",
            "description": "选择语音合成引擎类型",
            "combo_items": {
                "0": "System TTS",
                "1": "Edge TTS",
            },
        },
        "edge_tts_voice_name": {
            "name": "Edge TTS-语音名称",
            "description": "选择Edge TTS语音播报角色",
            "combo_items": {
                "0": "zh-CN-XiaoxiaoNeural",
                "1": "zh-CN-YunxiNeural",
                "2": "zh-CN-XiaoyiNeural",
                "3": "en-US-JennyNeural",
                "4": "en-US-GuyNeural",
            },
        },
        "voice_playback": {
            "name": "Voice playback device",
            "description": "选择语音播报播放设备",
            "combo_items": {
                "0": "System default",
                "1": "Speakers",
                "2": "Headphones",
                "3": "Bluetooth devices",
            },
        },
        "volume_size": {
            "name": "Speech volume",
            "description": "调整语音播报音量大小",
        },
        "speech_rate": {
            "name": "Speech rate",
            "description": "调整语音播报语速",
        },
        "system_volume_control": {
            "name": "System volume control",
            "description": "选择要控制的系统音量类型",
            "combo_items": {
                "0": "Main volume",
                "1": "App volume",
                "2": "System sound",
                "3": "Microphone volume",
            },
        },
        "system_volume_size": {
            "name": "System volume",
            "description": "调整系统音量大小",
        },
    },
}

specific_announcements = {
    "ZH_CN": {
        "title": {"name": "特定播报设置", "description": "配置特定结果的语音播报"},
        "enabled": {
            "name": "特定播报开关",
            "description": "开启或关闭特定结果语音播报的总开关",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "header": {"name": "开关"},
        "mode": {
            "name": "播报模式",
            "description": "选择语音播报模式",
            "combo_items": ["点名模式", "抽奖模式"],
        },
        "roll_call_title": {
            "name": "点名模式配置",
            "description": "配置点名模式下的语音播报",
        },
        "select_class_name": {
            "name": "选择班级/奖池",
            "description": "选择要管理TTS的班级或奖池",
        },
        "id_field": {"name": "学号"},
        "name_field": {"name": "姓名"},
        "prefix_field": {
            "name": "播报前缀",
            "description": "在播报内容前添加自定义文本",
        },
        "suffix_field": {
            "name": "播报后缀",
            "description": "在播报内容后添加自定义文本",
        },
        "lottery_title": {
            "name": "抽奖模式配置",
            "description": "配置抽奖模式下的语音播报",
        },
        "lottery_id_field": {"name": "序号"},
        "lottery_name_field": {"name": "名称"},
        "lottery_prefix_field": {
            "name": "抽奖前缀",
            "description": "在抽奖播报内容前添加自定义文本",
        },
        "lottery_suffix_field": {
            "name": "抽奖后缀",
            "description": "在抽奖播报内容后添加自定义文本",
        },
        "tts_alias": {
            "name": "替换名称",
            "description": "用于TTS发音的替换名称，留空则使用默认发音",
        },
    },
}
