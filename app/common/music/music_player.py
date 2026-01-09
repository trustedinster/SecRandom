# ==================================================
# 导入库
# ==================================================

import threading
import time
from typing import Optional
import numpy as np
import sounddevice as sd
import soundfile as sf
from loguru import logger

from app.tools.path_utils import *
from app.tools.settings_default import *
from app.tools.settings_access import *
from app.Language.obtain_language import *


# ==================================================
# 音乐播放器类
# ==================================================
class MusicPlayer:
    """音乐播放器类，用于在点名、闪抽动画和抽奖功能中播放背景音乐"""

    def __init__(self):
        """初始化音乐播放器"""
        self._current_music: Optional[str] = None
        self._is_playing: bool = False
        self._stop_flag: threading.Event = threading.Event()
        self._play_thread: Optional[threading.Thread] = None
        self._volume: float = 1.0  # 默认音量
        self._fade_in_duration: float = 0.0  # 渐入时长(秒)
        self._fade_out_duration: float = 0.0  # 渐出时长(秒)
        self._fade_out_thread: Optional[threading.Thread] = None

    def play_music(
        self,
        music_file: str,
        settings_group: str,
        loop: bool = True,
        fade_in: bool = True,
    ) -> bool:
        """播放音乐

        Args:
            music_file: 音乐文件名，空字符串表示不播放音乐
            settings_group: 设置组名，如"roll_call_settings"、"quick_draw_settings"等
            loop: 是否循环播放
            fade_in:是否使用渐入效果

        Returns:
            bool: 是否成功开始播放
        """
        from app.Language.obtain_language import get_content_name_async

        # 如果音乐文件为空或"无音乐"，则不播放
        if not music_file or music_file == get_content_name_async(
            "music_settings", "no_music"
        ):
            logger.debug("音乐文件为空或选择无音乐，不播放")
            return False

        # 停止当前播放的音乐
        self.stop_music()

        # 检查是否为随机播放
        is_random_play = music_file == get_content_name_async(
            "music_settings", "random_play"
        )

        # 获取音乐文件路径
        try:
            if is_random_play:
                # 随机播放：从音乐文件列表中随机选择一个
                from app.tools.path_utils import get_audio_path

                audio_dir = get_audio_path("music")
                if audio_dir.exists():
                    supported_formats = [".mp3", ".flac", ".wav", ".ogg"]
                    music_files = [
                        f.name
                        for f in audio_dir.iterdir()
                        if f.is_file() and f.suffix.lower() in supported_formats
                    ]
                    if music_files:
                        import random

                        music_file = random.choice(music_files)
                        logger.info(f"随机播放选择音乐: {music_file}")
                    else:
                        logger.warning("没有可用的音乐文件，无法随机播放")
                        return False
                else:
                    logger.warning("音乐目录不存在，无法随机播放")
                    return False

            music_path = get_audio_path(f"music/{music_file}")
            if not music_path.exists():
                logger.error(f"音乐文件不存在: {music_path}")
                return False
        except Exception as e:
            logger.error(f"获取音乐文件路径失败: {e}")
            return False

        # 从设置中获取音量和渐入渐出时长
        try:
            # 获取音量设置，默认为100%
            volume = readme_settings_async(
                settings_group, "animation_music_volume", 100
            )
            self._volume = volume / 100.0

            # 获取渐入时长设置
            if fade_in:
                fade_in_ms = readme_settings_async(
                    settings_group, "animation_music_fade_in", 0
                )
                self._fade_in_duration = fade_in_ms / 1000.0
            else:
                self._fade_in_duration = 0.0

            # 获取渐出时长设置
            fade_out_ms = readme_settings_async(
                settings_group, "animation_music_fade_out", 0
            )
            self._fade_out_duration = fade_out_ms / 1000.0
        except Exception as e:
            logger.error(f"获取音乐设置失败: {e}")
            self._volume = 1.0
            self._fade_in_duration = 0.0
            self._fade_out_duration = 0.0

        # 启动播放线程
        self._current_music = music_file
        self._stop_flag.clear()
        self._is_playing = True
        self._play_thread = threading.Thread(
            target=self._play_music_worker,
            args=(str(music_path), loop),
            daemon=True,
        )
        self._play_thread.start()

        logger.info(f"开始播放音乐: {music_file}, 音量: {self._volume}, 循环: {loop}")
        return True

    def stop_music(self, fade_out: bool = True) -> None:
        """停止播放音乐

        Args:
            fade_out: 是否使用渐出效果
        """
        if not self._is_playing:
            return

        logger.debug("停止播放音乐")

        # 如果需要渐出效果且当前有渐出时长设置
        if fade_out and self._fade_out_duration > 0 and self._is_playing:
            # 启动渐出线程
            self._fade_out_thread = threading.Thread(
                target=self._fade_out_worker, daemon=True
            )
            self._fade_out_thread.start()
            # 等待渐出完成
            self._fade_out_thread.join(timeout=self._fade_out_duration + 1.0)

        # 设置停止标志
        self._stop_flag.set()
        self._is_playing = False

        # 等待播放线程结束
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=2.0)

        self._current_music = None
        logger.debug("音乐已停止")

    def is_playing(self) -> bool:
        """检查是否正在播放音乐

        Returns:
            bool: 是否正在播放音乐
        """
        return self._is_playing

    def get_current_music(self) -> Optional[str]:
        """获取当前播放的音乐文件名

        Returns:
            Optional[str]: 当前播放的音乐文件名，如果没有播放则返回None
        """
        return self._current_music

    def _play_music_worker(self, music_path: str, loop: bool) -> None:
        """音乐播放工作线程（优化版，减少延迟）

        Args:
            music_path: 音乐文件路径
            loop: 是否循环播放
        """
        stream = None
        try:
            # 读取音乐文件（只读取一次）
            try:
                data, fs = sf.read(music_path)
                if len(data.shape) > 1 and data.shape[1] > 1:
                    data = np.mean(data, axis=1)
                data = data.astype(np.float32)
            except Exception as e:
                logger.error(f"读取音乐文件失败: {e}")
                return

            # 初始化音频流（只初始化一次）
            try:
                stream = sd.OutputStream(
                    samplerate=fs,
                    channels=1,
                    dtype="float32",
                    blocksize=4096,  # 增加块大小以减少系统调用
                )
                stream.start()
            except Exception as e:
                logger.error(f"初始化音频流失败: {e}")
                return

            # 计算渐入步数
            fade_in_steps = int(self._fade_in_duration * fs)
            fade_in_step = 0

            # 使用更大的块大小以提高性能
            chunk_size = 8192  # 增加到8192

            while not self._stop_flag.is_set():
                # 分块播放
                for i in range(0, len(data), chunk_size):
                    if self._stop_flag.is_set():
                        break

                    chunk = data[i : i + chunk_size].copy()

                    # 应用渐入效果
                    if fade_in_steps > 0 and fade_in_step < fade_in_steps:
                        remaining_steps = min(fade_in_steps - fade_in_step, len(chunk))
                        fade_in_factor = np.linspace(0, self._volume, remaining_steps)
                        chunk[:remaining_steps] *= fade_in_factor
                        if remaining_steps < len(chunk):
                            chunk[remaining_steps:] *= self._volume
                        fade_in_step += remaining_steps
                    else:
                        chunk *= self._volume

                    # 写入音频流
                    try:
                        stream.write(chunk)
                    except Exception as e:
                        logger.error(f"写入音频流失败: {e}")
                        break

                # 如果不循环或者收到停止信号，退出循环
                if not loop or self._stop_flag.is_set():
                    break

        except Exception as e:
            logger.error(f"音乐播放工作线程异常: {e}")
        finally:
            # 确保音频流关闭
            if stream:
                try:
                    stream.stop()
                    stream.close()
                except Exception as e:
                    logger.error(f"关闭音频流失败: {e}")
            self._is_playing = False
            logger.debug("音乐播放工作线程结束")

    def _fade_out_worker(self) -> None:
        """渐出效果工作线程"""
        if not self._is_playing or self._fade_out_duration <= 0:
            return

        logger.debug(f"开始音乐渐出，时长: {self._fade_out_duration}秒")

        # 计算渐出步数
        fade_out_steps = int(self._fade_out_duration * 50)  # 50Hz更新率
        fade_out_step = 0
        initial_volume = self._volume

        # 渐出效果循环
        while fade_out_step < fade_out_steps and not self._stop_flag.is_set():
            # 计算当前音量（线性递减）
            progress = fade_out_step / fade_out_steps
            self._volume = initial_volume * (1.0 - progress)

            # 等待下一帧
            time.sleep(1.0 / 50)  # 50Hz更新率
            fade_out_step += 1

        # 渐出完成，设置停止标志
        self._stop_flag.set()
        logger.debug("音乐渐出完成")


# 创建全局音乐播放器实例
music_player = MusicPlayer()


def get_music_files():
    """获取音乐文件列表

    Returns:
        List[str]: 音乐文件名列表，包含"无音乐"和"随机播放"选项
    """
    from app.tools.path_utils import get_audio_path
    from app.Language.obtain_language import get_content_name_async

    # 获取音频文件目录
    audio_dir = get_audio_path("music")
    # 确保目录存在
    from app.tools.path_utils import ensure_dir

    ensure_dir(audio_dir)

    # 获取音频文件列表
    music_files = [
        get_content_name_async("music_settings", "no_music")
    ]  # 无音乐选项，表示不使用音乐
    music_files.append(
        get_content_name_async("music_settings", "random_play")
    )  # 随机播放选项，表示随机选择音乐文件播放

    if audio_dir.exists():
        # 支持的音频格式
        supported_formats = [".mp3", ".flac", ".wav", ".ogg"]
        # 遍历目录获取所有支持的音频文件
        for file in audio_dir.iterdir():
            if file.is_file() and file.suffix.lower() in supported_formats:
                music_files.append(file.name)

    return music_files
