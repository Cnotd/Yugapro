"""Assessment pipeline that mirrors the thesis system architecture.

The pipeline owns the compute path only: video decoding, pose extraction,
feature calculation, model-enhanced feedback, rule fallback, and persistence
payload construction. HTTP routing and task scheduling live elsewhere.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from config.settings import get_pose_standard
from src.angle_calculator import AngleCalculator
from src.multimodal_client import MultimodalClient
from src.ollama_client import OllamaClient
from src.pose_detector import PoseDetector
from src.prompt_builder import PromptBuilder
from src.result_parser import ResultParser
from src.simple_evaluator import SimpleEvaluator
from src.stats_calculator import StatsCalculator
from src.video_reader import VideoReader


@dataclass
class AssessmentPipelineResult:
    # api_result 返回给前端展示，record_data 写入数据库归档。
    api_result: Dict[str, Any]
    record_data: Dict[str, Any]


class AssessmentPipeline:
    """Synchronous assessment workflow used inside a background thread."""

    def __init__(self, *, test_mode: bool = False) -> None:
        self.test_mode = test_mode
        self.video_reader: Optional[VideoReader] = None
        self.pose_detector: Optional[PoseDetector] = None
        self.angle_calculator: Optional[AngleCalculator] = None
        self.stats_calculator: Optional[StatsCalculator] = None
        self.prompt_builder: Optional[PromptBuilder] = None
        self.result_parser: Optional[ResultParser] = None
        self.simple_evaluator: Optional[SimpleEvaluator] = None
        self.multimodal_client: Optional[MultimodalClient] = None
        self.ollama_client: Optional[OllamaClient] = None
        self.multimodal_available = False
        self.ollama_available = False
        self._initialized = False
        self._init_lock = Lock()

    def _initialize_components(self) -> None:
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return
            # 各计算组件延迟初始化，避免 Flask 启动时就加载模型和外部客户端。
            self.video_reader = VideoReader()
            self.pose_detector = PoseDetector()
            self.angle_calculator = AngleCalculator()
            self.stats_calculator = StatsCalculator()
            self.prompt_builder = PromptBuilder()
            self.result_parser = ResultParser()
            self.simple_evaluator = SimpleEvaluator()
            self.multimodal_client = MultimodalClient()
            self.ollama_client = OllamaClient()
            # 外部模型不可用时不阻断主流程，后续会自动走本地规则兜底。
            self.multimodal_available = self._safe_check(self.multimodal_client)
            self.ollama_available = self._safe_check(self.ollama_client)
            self._initialized = True

    @staticmethod
    def _safe_check(client: Any) -> bool:
        try:
            return bool(client.check_connection())
        except Exception:
            return False

    def run(
        self,
        *,
        user_id: int,
        video_path: Path,
        original_filename: str,
        pose_name: str,
    ) -> AssessmentPipelineResult:
        if self.test_mode:
            return self._test_result(user_id, video_path, original_filename, pose_name)

        self._initialize_components()

        if not all(
            [
                self.video_reader,
                self.pose_detector,
                self.angle_calculator,
                self.stats_calculator,
                self.prompt_builder,
                self.result_parser,
                self.simple_evaluator,
            ]
        ):
            raise RuntimeError("Assessment pipeline was not initialized")

        start_time = time.time()

        # 主计算链路：视频帧 -> 姿态关键点 -> 角度序列 -> 统计特征。
        video_info, frames = self.video_reader.read(str(video_path))
        landmarks_seq = self.pose_detector.detect_sequence(frames)
        valid_landmarks = [item for item in landmarks_seq if item is not None]
        if not valid_landmarks:
            raise ValueError("No valid body landmarks were detected in the video")

        angles_seq = self.angle_calculator.compute_all(landmarks_seq)
        stats = self.stats_calculator.compute(angles_seq)
        raw_stability = self.stats_calculator.compute_stability(landmarks_seq)

        pose_standard = get_pose_standard(pose_name) or {}
        # 提示词只承载结构化事实和动作标准，避免模型凭空决定评分依据。
        prompt = self.prompt_builder.build(stats, raw_stability, pose_name, pose_standard)
        assessment_result = self._run_model_or_fallback(
            frames=frames,
            prompt=prompt,
            stats=stats,
            stability_score=raw_stability,
            pose_name=pose_name,
            pose_standard=pose_standard,
        )

        api_result = self._normalize_result(assessment_result, stats)
        record_data = self._build_record(
            user_id=user_id,
            video_path=video_path,
            original_filename=original_filename,
            pose_name=pose_name,
            video_info=video_info,
            frame_count=len(frames),
            raw_stability=raw_stability,
            api_result=api_result,
            processing_time=round(time.time() - start_time, 2),
        )
        return AssessmentPipelineResult(api_result=api_result, record_data=record_data)

    def _run_model_or_fallback(
        self,
        *,
        frames: list,
        prompt: str,
        stats: Dict[str, Any],
        stability_score: float,
        pose_name: str,
        pose_standard: Dict[str, Any],
    ) -> Dict[str, Any]:
        key_frame = frames[len(frames) // 2] if frames else None

        # 优先使用在线多模态模型；解析失败或请求异常时，继续尝试其他通道。
        if self.multimodal_available and self.multimodal_client and key_frame is not None:
            try:
                response = self.multimodal_client.analyze_image_with_prompt(key_frame, prompt)
                parsed = self.result_parser.parse(response) if self.result_parser else {}
                if parsed.get("success"):
                    return parsed
            except Exception:
                pass

        if self.ollama_available and self.ollama_client and key_frame is not None:
            try:
                response = self.ollama_client.generate(prompt, key_frame)
                parsed = self.result_parser.parse(response) if self.result_parser else {}
                if parsed.get("success"):
                    return parsed
            except Exception:
                pass

        # 最后一层兜底：只依赖本地角度统计和规则库，保证断网时仍有结果。
        return self.simple_evaluator.evaluate(
            stats,
            stability_score,
            pose_name,
            pose_standard,
        )

    @staticmethod
    def _normalize_result(assessment_result: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        # 不同模型返回格式可能不完全一致，这里统一整理成前端稳定消费的字段。
        data = assessment_result.get("data", {}) if isinstance(assessment_result, dict) else {}
        score = data.get("score", {}) if isinstance(data, dict) else {}

        total_score = float(score.get("total", 80) or 80)
        structure_score = float(score.get("accuracy", 50) or 50)
        alignment_score = float(score.get("stability", 25) or 25)
        stability_score = float(score.get("coordination", 5) or 5)

        problems = data.get("problems", []) if isinstance(data, dict) else []
        suggestions = data.get("suggestions", []) if isinstance(data, dict) else []

        return {
            "total_score": total_score,
            "structure_score": structure_score,
            "alignment_score": alignment_score,
            "stability_score": stability_score,
            "angle_data": stats,
            "problems": problems if isinstance(problems, list) else [],
            "suggestions": suggestions if isinstance(suggestions, list) else [],
        }

    @staticmethod
    def _build_record(
        *,
        user_id: int,
        video_path: Path,
        original_filename: str,
        pose_name: str,
        video_info: Dict[str, Any],
        frame_count: int,
        raw_stability: float,
        api_result: Dict[str, Any],
        processing_time: float,
    ) -> Dict[str, Any]:
        width = video_info.get("width", 0) if isinstance(video_info, dict) else 0
        height = video_info.get("height", 0) if isinstance(video_info, dict) else 0
        # 数据库记录保留视频元信息、评分、问题和建议，便于历史回看与排障。
        return {
            "user_id": user_id,
            "video_name": original_filename,
            "video_path": str(video_path),
            "pose_name": pose_name,
            "total_score": api_result["total_score"],
            "structure_score": api_result["structure_score"],
            "alignment_score": api_result["alignment_score"],
            "stability_score": api_result["stability_score"],
            "angle_data": api_result["angle_data"],
            "graph_data": {},
            "stability_rating": raw_stability,
            "problems": api_result["problems"],
            "suggestions": api_result["suggestions"],
            "annotated_video_path": None,
            "video_duration": video_info.get("duration") if isinstance(video_info, dict) else None,
            "video_fps": video_info.get("fps") if isinstance(video_info, dict) else None,
            "video_resolution": f"{width}x{height}",
            "frame_count": frame_count,
            "processing_time": processing_time,
            "model_used": "qwen" if api_result.get("suggestions") else "simple_evaluator",
        }

    @staticmethod
    def _test_result(
        user_id: int,
        video_path: Path,
        original_filename: str,
        pose_name: str,
    ) -> AssessmentPipelineResult:
        api_result = {
            "total_score": 88.0,
            "structure_score": 52.0,
            "alignment_score": 28.0,
            "stability_score": 8.0,
            "angle_data": {
                "left_elbow": 170,
                "right_elbow": 168,
                "left_knee": 175,
                "right_knee": 174,
                "left_hip": 160,
                "right_hip": 161,
            },
            "problems": ["Test mode placeholder issue"],
            "suggestions": ["Test mode placeholder suggestion"],
        }
        record_data = {
            "user_id": user_id,
            "video_name": original_filename,
            "video_path": str(video_path),
            "pose_name": pose_name,
            "total_score": api_result["total_score"],
            "structure_score": api_result["structure_score"],
            "alignment_score": api_result["alignment_score"],
            "stability_score": api_result["stability_score"],
            "angle_data": api_result["angle_data"],
            "graph_data": {},
            "stability_rating": api_result["stability_score"],
            "problems": api_result["problems"],
            "suggestions": api_result["suggestions"],
            "annotated_video_path": None,
            "video_duration": 0,
            "video_fps": 0,
            "video_resolution": "0x0",
            "frame_count": 0,
            "processing_time": 0,
            "model_used": "test_mode",
        }
        return AssessmentPipelineResult(api_result=api_result, record_data=record_data)
