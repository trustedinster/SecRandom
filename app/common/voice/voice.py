"""
语音播报模块
提供基于 edge-tts / pyttsx3 的跨平台语音合成与播放能力，
并内置缓存、队列、负载均衡与权限控制。
"""

# --------- 标准库 ---------
import json
import asyncio
import concurrent.futures
import os
import platform
import queue
import sys
import threading
import time
from collections import OrderedDict
from io import BytesIO
from queue import Queue, Empty
from typing import Any, Dict, List, Optional, Tuple, Union

# --------- 第三方库 ---------
import edge_tts
import numpy as np
import psutil
import pyttsx3
import sounddevice as sd
import soundfile as sf
from loguru import logger
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# --------- 项目内部 ---------
from app.tools.path_utils import ensure_dir, get_audio_path
from app.tools.settings_access import readme_settings_async
from app.tools.config import restore_volume


# 权限检查装饰器
def require_permission(permission: str):
    """权限检查装饰器"""

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # 这里可以添加具体的权限检查逻辑
            # 示例：检查当前用户是否有使用TTS的权限
            has_perm = True  # 实际实现时替换为真实权限检查
            if not has_perm:
                logger.error(f"权限不足，无法执行 {func.__name__}")
                return
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class VoicePlaybackSystem:
    """语音播报核心引擎"""

    def __init__(self):
        self.play_queue: Queue[Union[Tuple[np.ndarray, int], str]] = Queue(
            maxsize=20
        )  # 限制队列防止内存溢出
        self._stop_flag: threading.Event = threading.Event()
        self._play_thread: Optional[threading.Thread] = None
        self._load_balancer: LoadBalancer = LoadBalancer()
        self._is_playing: bool = False  # 播放状态标志
        self._is_playing_lock: threading.Lock = (
            threading.Lock()
        )  # 保护_is_playing标志的线程锁
        self._volume: float = 1.0  # 默认音量值100%
        self._speed: int = 100  # 默认语速100%

    def set_volume(self, volume: float) -> None:
        """设置播放音量，范围0.0-1.0"""
        # 输入验证
        if not isinstance(volume, (int, float)):
            logger.error(f"无效的音量值: {volume}")
            return
        self._volume = max(0.0, min(1.0, float(volume)))

    def set_speed(self, speed: int) -> None:
        """设置播放语速，范围0-200"""
        # 输入验证
        if not isinstance(speed, int):
            logger.error(f"无效的语速值: {speed}")
            return
        self._speed = max(0, min(200, speed))

    def start(self) -> None:
        """启动播放系统"""
        if self._play_thread is None:
            self._stop_flag.clear()
            self._play_thread = threading.Thread(
                target=self._playback_worker, daemon=True, name="VoicePlaybackThread"
            )
            self._play_thread.start()

    def _playback_worker(self) -> None:
        """播放线程主循环"""
        while not self._stop_flag.is_set():
            try:
                # 非阻塞获取任务，设置超时时间避免无限等待
                timeout = 0.1  # 短暂超时，平衡响应速度和CPU占用
                task = self.play_queue.get(timeout=timeout)
                logger.debug(f"获取到播放任务: {type(task).__name__}")

                # 只有在有实际播放任务时，才进行系统负载检测和队列大小调整
                new_queue_size = self._load_balancer.get_optimal_queue_size()
                if self.play_queue.maxsize != new_queue_size:
                    self.play_queue.maxsize = new_queue_size
                    logger.debug(f"队列大小调整为: {new_queue_size}")

                # 处理两种任务格式：文件路径或内存数据
                if isinstance(task, tuple):  # 内存数据
                    data, fs = task
                    logger.debug(f"处理内存数据: 数据长度={len(data)}, 采样率={fs}")
                    self._safe_play(data, fs)
                else:  # 文件路径
                    try:
                        logger.debug(f"处理文件路径: {task}")
                        data, fs = sf.read(task)
                        logger.debug(f"读取文件成功: 数据长度={len(data)}, 采样率={fs}")
                        self._safe_play(data, fs)
                    except Exception as e:
                        logger.error(f"读取音频文件失败: {e}", exc_info=True)

            except Empty:
                # 队列为空时，短暂休息避免CPU占用过高
                time.sleep(0.1)
                continue
            except Exception as e:
                logger.error(f"播放线程异常: {e}", exc_info=True)
                # 短暂休息后继续，避免异常风暴
                time.sleep(0.5)

    def _safe_play(self, data: np.ndarray, fs: int) -> None:
        """安全播放实现

        注意：添加了更完善的异常处理和日志，确保播放失败不会导致程序崩溃
        """
        stream = None
        try:
            # 计算语速调整因子，1.0表示正常语速
            speed_factor: float = self._speed / 100.0

            # 根据语速调整采样率
            adjusted_fs: int = int(fs * speed_factor)
            logger.debug(
                f"准备播放：原始采样率={fs}，调整后采样率={adjusted_fs}，音量={self._volume}"
            )

            # 限制音频数据大小，防止内存溢出（最多1分钟音频）
            max_samples = int(fs * 60)  # 1分钟音频
            if len(data) > max_samples:
                logger.warning("音频数据过长，已截断至1分钟")
                data = data[:max_samples]
            logger.debug(
                f"音频数据：长度={len(data)}，类型={data.dtype}，通道数={data.shape[1] if len(data.shape) > 1 else 1}"
            )

            # 确保音频数据是单通道
            if len(data.shape) > 1 and data.shape[1] > 1:
                logger.info("将多通道音频转换为单通道")
                data = np.mean(data, axis=1)

            # 初始化音频流，添加设备验证逻辑
            stream = sd.OutputStream(
                samplerate=adjusted_fs,
                channels=1,
                dtype="float32",
                blocksize=2048,  # 优化实时性
            )
            stream.start()
            logger.debug("音频流已启动")

            with self._is_playing_lock:
                self._is_playing = True  # 开始播放
            logger.info("开始播放音频")

            # 分块写入避免卡顿
            chunk_size: int = 4096
            for i in range(0, len(data), chunk_size):
                if self._stop_flag.is_set():
                    logger.info("收到停止信号，中断播放")
                    break

                chunk = data[i : i + chunk_size]
                # 应用音量控制，将数据乘以音量系数
                chunk = chunk * self._volume
                # 数据类型转换中，float64→float32，完美适配
                chunk = chunk.astype(np.float32)

                # 写入音频流
                stream.write(chunk)

            logger.info("音频播放完毕")
            with self._is_playing_lock:
                self._is_playing = False  # 播放结束

        except sd.PortAudioError as e:
            logger.error(f"PortAudio错误：{e}", exc_info=True)
            # 处理PortAudio特定错误，避免程序崩溃
            with self._is_playing_lock:
                self._is_playing = False
        except Exception as e:
            logger.error(f"播放音频失败：{e}", exc_info=True)
            # 确保播放状态正确重置，避免死锁
            with self._is_playing_lock:
                self._is_playing = False
        finally:
            # 确保音频流正确关闭
            if stream:
                try:
                    stream.stop()
                    stream.close()
                    logger.debug("音频流已关闭")
                except Exception as e:
                    logger.error(f"关闭音频流失败：{e}", exc_info=True)

    def add_task(self, task: Union[Tuple[np.ndarray, int], str]) -> bool:
        """添加播放任务（线程安全）"""
        try:
            # 输入验证
            if isinstance(task, tuple):  # 内存数据
                if len(task) != 2:
                    logger.error(f"无效的任务格式: {task}")
                    return False
                data, fs = task
                if not isinstance(data, np.ndarray) or not isinstance(fs, int):
                    logger.error("无效的内存数据格式")
                    return False
            else:  # 文件路径
                if not isinstance(task, str) or not task:
                    logger.error("无效的文件路径")
                    return False

            self.play_queue.put_nowait(task)
            return True
        except queue.Full:
            logger.error("播放队列已满，丢弃新任务")
            return False
        except Exception as e:
            logger.error(f"添加播放任务失败: {e}")
            return False

    def stop(self) -> None:
        """停止所有播放"""
        if self._stop_flag.is_set():
            return

        self._stop_flag.set()
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=5.0)  # 添加超时保护
        self._clear_queue()
        # 重置线程状态，允许下次调用start()重新启动
        self._play_thread = None
        self._stop_flag.clear()

    def _clear_queue(self) -> None:
        """清空播放队列"""
        while not self.play_queue.empty():
            try:
                self.play_queue.get_nowait()
            except Empty:
                break


class VoiceCacheManager:
    """智能语音缓存系统"""

    # 智能语音缓存系统
    # 内存缓存大小限制（条）
    MEMORY_CACHE_SIZE = 100
    # 缓存过期时间（秒）
    CACHE_EXPIRY_TIME = 3600 * 24  # 24小时
    # 清理间隔时间（秒）
    CLEANUP_INTERVAL = 3600  # 1小时

    def __init__(self, audio_dir: Optional[str] = None):
        self.audio_dir: str = audio_dir if audio_dir else get_audio_path("voices")
        ensure_dir(self.audio_dir)
        # 使用OrderedDict实现LRU缓存
        self._memory_cache: Dict[str, Tuple[np.ndarray, int]] = OrderedDict()
        self._disk_cache_lock: threading.Lock = threading.Lock()
        self._memory_cache_lock: threading.Lock = threading.Lock()
        self._last_cleanup_time: float = time.time()

        # 启动缓存清理线程
        self._cleanup_thread: threading.Thread = threading.Thread(
            target=self._cache_cleanup_worker,
            daemon=True,
            name="VoiceCacheCleanupThread",
        )
        self._cleanup_thread.start()

    def get_voice(self, text: str, voice: str) -> Tuple[np.ndarray, int]:
        """获取语音数据（自动缓存）"""
        # 输入验证
        if not isinstance(text, str) or not text:
            logger.error(f"无效的文本: {text}")
            raise ValueError("文本不能为空")
        if not isinstance(voice, str) or not voice:
            logger.error(f"无效的语音名称: {voice}")
            raise ValueError("语音名称不能为空")

        logger.info(f"获取语音: text='{text}', voice='{voice}'")

        # 检查并执行缓存清理
        self._check_and_cleanup()

        # 1. 检查内存缓存
        cache_key: str = self._generate_cache_key(text, voice)
        with self._memory_cache_lock:
            if cache_key in self._memory_cache:
                logger.debug(f"命中内存缓存: {cache_key}")
                # 移到末尾表示最近使用
                self._memory_cache.move_to_end(cache_key)
                return self._memory_cache[cache_key]

        # 2. 检查磁盘缓存
        file_path: str = self._get_cache_file_path(text, voice)
        if os.path.exists(file_path):
            logger.debug(f"命中磁盘缓存: {file_path}")
            try:
                data, fs = sf.read(file_path)
                # 更新文件的访问时间和修改时间，延长缓存有效期
                current_time = time.time()
                os.utime(file_path, times=(current_time, current_time))
                # 加入内存缓存
                self._add_to_memory_cache(cache_key, data, fs)
                return data, fs
            except Exception as e:
                logger.error(f"读取缓存失败: {e}")
        else:
            logger.debug(f"未命中缓存，生成新语音: {cache_key}")

        # 3. 实时生成并缓存
        data, fs = asyncio.run(self._generate_voice(text, voice))

        # 异步保存到磁盘
        threading.Thread(
            target=self._save_to_disk, args=(file_path, data, fs), daemon=True
        ).start()

        # 加入内存缓存
        self._add_to_memory_cache(cache_key, data, fs)
        return data, fs

    async def _generate_voice(self, text: str, voice: str) -> Tuple[np.ndarray, int]:
        """生成语音核心方法"""
        # 限制文本长度，防止生成过大的音频
        max_text_length = 500
        if len(text) > max_text_length:
            text = text[:max_text_length]
            logger.warning(f"文本长度超过限制{max_text_length}，已截断")

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                communicate = edge_tts.Communicate(text=text, voice=voice)

                audio_buffer = BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buffer.write(chunk["data"])
                audio_buffer.seek(0)  # 重置指针位置
                return sf.read(audio_buffer)
            except Exception as e:
                retry_count += 1
                logger.error(f"生成语音失败，重试{retry_count}/{max_retries}: {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(1)  # 重试间隔1秒

        # 最终失败时的降级处理
        logger.error("生成语音失败，已达到最大重试次数")
        raise RuntimeError("生成语音失败")

    def _generate_cache_key(self, text: str, voice: str) -> str:
        """生成缓存键，使用语音模型名称和文本的组合"""
        # 生成安全的文件名，移除或替换不安全的字符
        safe_text = (
            text.replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace('"', "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
        )
        return f"{voice}_{safe_text}"

    def _get_cache_file_path(self, text: str, voice: str) -> str:
        """获取缓存文件路径，使用语音模型名称和学生/奖品名称作为文件名"""
        # 生成安全的文件名，移除或替换不安全的字符
        safe_text = (
            text.replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace('"', "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
        )
        filename = f"{voice}_{safe_text}.wav"
        return os.path.join(self.audio_dir, filename)

    def _add_to_memory_cache(self, cache_key: str, data: np.ndarray, fs: int) -> None:
        """添加到内存缓存，实现LRU机制"""
        with self._memory_cache_lock:
            if cache_key in self._memory_cache:
                # 如果已存在，移到末尾
                self._memory_cache.move_to_end(cache_key)
            else:
                # 检查是否超过容量限制
                if len(self._memory_cache) >= self.MEMORY_CACHE_SIZE:
                    # 删除最久未使用的项
                    self._memory_cache.popitem(last=False)
                # 添加新项到末尾
                self._memory_cache[cache_key] = (data, fs)

    def _save_to_disk(self, file_path: str, data: np.ndarray, fs: int) -> None:
        """异步保存到磁盘"""
        try:
            with self._disk_cache_lock:
                sf.write(file_path, data, fs)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def _check_and_cleanup(self) -> None:
        """检查并执行缓存清理"""
        current_time: float = time.time()
        if current_time - self._last_cleanup_time >= self.CLEANUP_INTERVAL:
            # 执行清理
            self._cleanup_expired_cache()
            self._last_cleanup_time = current_time

    def _cache_cleanup_worker(self) -> None:
        """缓存清理线程"""
        while True:
            time.sleep(self.CLEANUP_INTERVAL)
            self._cleanup_expired_cache()

    def _cleanup_expired_cache(self) -> None:
        """清理过期缓存文件

        注意：根据需求，本地音频文件不会过期，所以此方法不再删除文件
        但保留缓存清理线程，以便未来扩展其他清理逻辑
        """
        try:
            logger.info("缓存清理：本地音频文件不会过期，跳过文件删除")
            # 可以在这里添加其他清理逻辑，如日志清理等
        except Exception as e:
            logger.error(f"缓存清理失败: {e}")


class LoadBalancer:
    """系统负载均衡器"""

    # 基础队列大小设置
    BASE_QUEUE_SIZE: int = 3  # 基础队列大小(最低3人)
    MAX_QUEUE_SIZE: int = 100  # 最大队列大小，防止无限增长

    # CPU负载阈值与对应的队列大小系数（按CPU使用率从低到高排序）
    CPU_THRESHOLDS: list[tuple[float, float]] = [
        (0, 1.0),  # CPU ≤ 10%: 正常系数
        (10, 0.9),  # 10% < CPU ≤ 20%: 略降系数
        (20, 0.8),  # 20% < CPU ≤ 30%: 降低系数
        (30, 0.7),  # 30% < CPU ≤ 40%: 进一步降低
        (40, 0.6),  # 40% < CPU ≤ 50%: 继续降低
        (50, 0.5),  # 50% < CPU ≤ 60%: 中等负载
        (60, 0.4),  # 60% < CPU ≤ 70%: 较高负载
        (70, 0.3),  # 70% < CPU ≤ 80%: 高负载
        (80, 0.2),  # 80% < CPU ≤ 90%: 很高负载
        (90, 0.1),  # CPU > 90%: 极高负载
    ]

    # 内存负载阈值与对应的队列大小系数（按可用内存从低到高排序）
    MEMORY_THRESHOLDS: list[tuple[float, float]] = [
        (0, 0.2),  # 内存 < 0.5GB: 极低内存，大幅降低队列
        (0.5, 0.3),  # 0.5GB ≤ 内存 < 1GB: 低内存，降低队列
        (1, 0.5),  # 1GB ≤ 内存 < 2GB: 中等偏低内存，适当降低
        (2, 0.7),  # 2GB ≤ 内存 < 4GB: 中等内存，略微降低
        (4, 0.8),  # 4GB ≤ 内存 < 8GB: 较充足内存，小幅降低
        (8, 0.9),  # 8GB ≤ 内存 < 16GB: 充足内存，略降
        (16, 0.95),  # 16GB ≤ 内存 < 32GB: 很充足内存，微调
        (32, 1.0),  # 32GB ≤ 内存 < 64GB: 充足内存，正常系数
        (64, 1.0),  # 内存 ≥ 64GB: 非常充足内存，正常系数
    ]

    def get_optimal_queue_size(self) -> int:
        """根据系统负载动态调整队列大小"""
        try:
            # 获取系统负载情况
            cpu_percent: float = psutil.cpu_percent()
            mem_available: float = psutil.virtual_memory().available / (
                1024**3
            )  # GB(可用内存)
            mem_percent: float = psutil.virtual_memory().percent  # 内存使用率%

            # 参数有效性检查
            if (
                not isinstance(cpu_percent, (int, float))
                or cpu_percent < 0
                or cpu_percent > 100
            ):
                logger.error("CPU使用率异常，使用基础队列大小")
                return self.BASE_QUEUE_SIZE

            if not isinstance(mem_available, (int, float)) or mem_available < 0:
                logger.error("内存信息异常，使用基础队列大小")
                return self.BASE_QUEUE_SIZE

            # 计算基于CPU的队列大小调整系数
            cpu_factor: float = 1.0
            for threshold, factor in self.CPU_THRESHOLDS:
                if cpu_percent > threshold:
                    cpu_factor = factor
                else:
                    break

            # 计算基于内存的队列大小调整系数
            mem_factor: float = 1.0
            for threshold, factor in self.MEMORY_THRESHOLDS:
                if mem_available > threshold:
                    mem_factor = factor
                else:
                    break

            # 计算动态队列基础值（根据系统资源情况）
            # 可用内存越多，动态基础值越大
            dynamic_base = self.BASE_QUEUE_SIZE + int(
                mem_available * 5
            )  # 每GB内存增加5个队列位置

            # 结合CPU和内存负载，计算最终队列大小
            # 使用几何平均计算综合系数，更合理地平衡CPU和内存负载
            combined_factor = (cpu_factor * mem_factor) ** 0.5
            queue_size: int = int(dynamic_base * combined_factor)

            # 确保队列大小在合理范围内
            queue_size = max(self.BASE_QUEUE_SIZE, min(queue_size, self.MAX_QUEUE_SIZE))

            logger.debug(
                f"系统负载 (CPU:{cpu_percent}%, 内存使用率:{mem_percent}%, 可用内存:{mem_available:.2f}GB) "
                f"→ CPU系数:{cpu_factor}, 内存系数:{mem_factor}, 综合系数:{combined_factor:.2f} "
                f"→ 队列大小设为{queue_size}"
            )
            return queue_size
        except Exception as e:
            # 异常处理，确保方法总是返回有效值
            logger.error(f"获取系统负载信息失败: {e}，使用基础队列大小")
            return self.BASE_QUEUE_SIZE


class TTSHandler:
    """语音处理主控制器"""

    def __init__(self):
        self.playback_system: VoicePlaybackSystem = VoicePlaybackSystem()
        self.cache_manager: VoiceCacheManager = VoiceCacheManager()
        self.playback_system.start()
        self.voice_engine: Optional[Any] = None
        self.system_tts_lock: threading.Lock = (
            threading.Lock()
        )  # 系统TTS线程锁，防止冲突

        # 使用线程池管理异步任务
        self._thread_pool: concurrent.futures.ThreadPoolExecutor = (
            concurrent.futures.ThreadPoolExecutor(
                max_workers=4,  # 限制线程数量
                thread_name_prefix="TTSWorker",
            )
        )

        # 跨平台TTS引擎初始化
        self._init_tts_engine()

    def _init_tts_engine(self) -> None:
        """跨平台TTS引擎初始化"""
        try:
            system: str = platform.system()

            if system == "Windows":
                # Windows平台支持检查
                if (
                    sys.platform == "win32"
                    and sys.getwindowsversion().major >= 10
                    and platform.machine() != "x86"
                ):
                    if not hasattr(
                        QApplication.instance(), "pumping_reward_voice_engine"
                    ):
                        QApplication.instance().pumping_reward_voice_engine = (
                            pyttsx3.init()
                        )
                        QApplication.instance().pumping_reward_voice_engine.startLoop(
                            False
                        )
                    self.voice_engine = (
                        QApplication.instance().pumping_reward_voice_engine
                    )
                    logger.info("Windows系统TTS引擎初始化成功")
                else:
                    logger.error(
                        "Windows系统TTS引擎需要Windows 10及以上系统且非x86架构"
                    )

            elif system == "Linux":
                # Linux平台TTS引擎初始化
                try:
                    # 检查espeak是否可用
                    import subprocess

                    result = subprocess.run(
                        ["which", "espeak"], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        if not hasattr(
                            QApplication.instance(), "pumping_reward_voice_engine"
                        ):
                            QApplication.instance().pumping_reward_voice_engine = (
                                pyttsx3.init()
                            )
                            QApplication.instance().pumping_reward_voice_engine.startLoop(
                                False
                            )
                        self.voice_engine = (
                            QApplication.instance().pumping_reward_voice_engine
                        )
                        logger.info("Linux系统TTS引擎初始化成功 (使用espeak)")
                    else:
                        logger.error(
                            "Linux系统TTS引擎需要安装espeak: sudo apt-get install espeak"
                        )
                except Exception as e:
                    logger.error(f"Linux系统TTS引擎初始化失败: {e}")

            else:
                logger.error(f"不支持的操作系统: {system}，系统TTS功能不可用")

        except Exception as e:
            logger.error(f"TTS引擎初始化失败: {e}")
            self.voice_engine = None

    @require_permission("tts.use")
    def voice_play(
        self,
        config: Dict[str, Any],
        student_names: List[str],
        engine_type: int,
        voice_name: str,
        class_name: str = "",
    ) -> None:
        """主入口函数"""
        # 输入验证
        if not isinstance(config, dict):
            logger.error(f"无效的配置: {config}")
            return
        if not isinstance(student_names, list):
            logger.error(f"无效的学生名单: {student_names}")
            return
        if engine_type not in [0, 1]:
            logger.error(f"无效的引擎类型: {engine_type}")
            return
        if not isinstance(voice_name, str):
            logger.error(f"无效的语音名称: {voice_name}")
            return

        try:
            if not student_names:
                return

            # 停止之前的播放，清空队列
            self.stop()
            # 重新启动播放线程
            self.playback_system.start()

            # 读取音频设置文件
            audio_settings = {}
            if class_name:
                audio_file = get_audio_path(f"{class_name}.json")
                if audio_file.exists():
                    with open(str(audio_file), "r", encoding="utf-8") as f:
                        audio_settings = json.load(f)

            # 应用TTS别名、前缀和后缀
            processed_names = []
            for name in student_names:
                # 获取对应的音频设置，如果不存在则使用默认值
                settings = audio_settings.get(name, {})
                tts_alias = settings.get("tts_alias", "")
                prefix = settings.get("prefix", "")
                suffix = settings.get("suffix", "")

                # 构建最终的播报文本
                announcement_text = []
                if prefix:
                    announcement_text.append(prefix)
                if tts_alias:
                    announcement_text.append(tts_alias)
                else:
                    announcement_text.append(name)
                if suffix:
                    announcement_text.append(suffix)

                processed_names.append(" ".join(announcement_text))

            # 添加日志，记录要播放的学生名单
            logger.debug(f"准备播放语音，原始学生名单: {student_names}")
            logger.debug(f"处理后学生名单: {processed_names}")
            logger.debug(f"语音引擎类型: {engine_type}，语音名称: {voice_name}")

            # 系统TTS处理
            if engine_type == 0:
                logger.debug(f"使用系统TTS播放，配置: {config}")
                self._handle_system_tts(processed_names, config)
                logger.info("系统TTS播报")

            # Edge TTS处理
            elif engine_type == 1:
                logger.debug(f"使用Edge TTS播放，配置: {config}")
                self._handle_edge_tts(processed_names, config, voice_name)
                logger.info("Edge TTS播报")

        except Exception as e:
            logger.error(f"语音播报失败: {e}", exc_info=True)

    def _handle_system_tts(
        self, student_names: List[str], config: Dict[str, Any]
    ) -> None:
        """系统TTS处理"""
        # 检查是否开启系统音量控制（增强错误处理，防止崩溃）
        try:
            system_volume_control = readme_settings_async(
                "basic_voice_settings", "system_volume_control"
            )
            if system_volume_control:
                # 获取系统音量大小并设置
                system_volume_size = readme_settings_async(
                    "basic_voice_settings", "system_volume_size"
                )
                # 确保音量值是整数
                if isinstance(system_volume_size, (int, str)):
                    restore_volume(int(system_volume_size))
        except Exception as e:
            logger.error(f"系统音量控制处理失败: {e}")
            # 继续执行，不影响语音播报

        with self.system_tts_lock:
            if self.voice_engine is None:
                logger.error("系统TTS引擎未初始化，无法播放语音")
                return
            for name in student_names:
                try:
                    self.voice_engine.say(f"{name}")
                    self.voice_engine.iterate()
                except Exception as e:
                    logger.error(f"处理{name}失败: {e}")

    def _init_system_tts(self, config: Dict[str, Any]) -> Optional[Any]:
        """初始化系统TTS引擎（跨平台支持）"""
        try:
            engine = pyttsx3.init()
            engine.setProperty("volume", config["voice_volume"] / 100.0)
            engine.setProperty("rate", int(200 * (config["voice_speed"] / 100)))

            # 语音模型设置
            voices = engine.getProperty("voices")
            voice_found = False
            for voice in voices:
                if config["system_voice_name"] in voice.id:
                    engine.setProperty("voice", voice.id)
                    voice_found = True
                    break

            if not voice_found and voices:
                # 如果找不到指定语音，使用第一个可用语音
                engine.setProperty("voice", voices[0].id)
                logger.info(f"未找到语音'{config['system_voice_name']}'，使用默认语音")

            return engine

        except Exception as e:
            logger.error(f"初始化系统TTS引擎失败: {e}")
            return None

    def _handle_edge_tts(
        self, student_names: List[str], config: Dict[str, Any], voice_name: str
    ) -> None:
        """Edge TTS处理模块启动"""
        # 使用线程池执行任务
        self._thread_pool.submit(
            self._prepare_and_play, student_names, config, voice_name
        )

    def _prepare_and_play(
        self, student_names: List[str], config: Dict[str, Any], voice_name: str
    ) -> None:
        """准备并播放语音"""
        # 检查是否开启系统音量控制（增强错误处理，防止崩溃）
        try:
            system_volume_control = readme_settings_async(
                "basic_voice_settings", "system_volume_control"
            )
            if system_volume_control:
                # 获取系统音量大小并设置
                system_volume_size = readme_settings_async(
                    "basic_voice_settings", "system_volume_size"
                )
                # 确保音量值是整数
                if isinstance(system_volume_size, (int, str)):
                    restore_volume(int(system_volume_size))
        except Exception as e:
            logger.error(f"系统音量控制处理失败: {e}")
            # 继续执行，不影响语音播报

        # 设置播放音量，转换为0.0-1.0范围
        self.playback_system.set_volume(config["voice_volume"] / 100.0)
        # 设置播放语速
        self.playback_system.set_speed(config["voice_speed"])

        for name in student_names:
            try:
                # 获取语音数据（自动缓存）
                data, fs = self.cache_manager.get_voice(name, voice_name)
                # 提交播放任务
                if not self.playback_system.add_task((data, fs)):
                    logger.error(f"提交播放任务失败: {name}")
            except Exception as e:
                logger.error(f"处理{name}失败: {e}")

        logger.debug("所有语音播放任务已提交，将异步播放")

    def stop(self) -> None:
        """停止所有播放

        注意：不会关闭线程池，仅停止当前播放任务
        线程池将在对象销毁时自动关闭
        """
        self.playback_system.stop()

        # 系统TTS引擎也需要停止
        with self.system_tts_lock:
            if self.voice_engine is not None:
                try:
                    self.voice_engine.stop()
                except Exception as e:
                    logger.error(f"停止系统TTS引擎失败: {e}")
