"""
结果解析模块
解析大模型返回的评估结果
"""

import json
import re
from typing import Dict, List, Optional, Tuple


class ResultParser:
    """结果解析器"""
    
    def __init__(self):
        pass
    
    def parse(self, response: str) -> Dict:
        """
        解析模型返回的评估结果
        
        Args:
            response: 模型返回的原始文本
            
        Returns:
            result: 解析后的结果字典
        """
        # 尝试提取JSON部分
        json_str = self._extract_json(response)
        
        if json_str:
            try:
                data = json.loads(json_str)
                
                # 验证数据结构
                validated_data = self._validate_and_clean(data)
                
                return {
                    "success": True,
                    "data": validated_data,
                    "raw": response
                }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"JSON解析失败: {str(e)}",
                    "raw": response
                }
        else:
            # 如果没有找到JSON,尝试从文本中提取信息
            return self._parse_from_text(response)
    
    def _extract_json(self, text: str) -> Optional[str]:
        """
        从文本中提取JSON部分
        
        Args:
            text: 原始文本
            
        Returns:
            JSON字符串,未找到返回None
        """
        # 查找```json和```之间的内容
        pattern = r'```json\s*(.*?)\s*```'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # 尝试查找单纯的{...} JSON对象
        pattern = r'\{[\s\S]*\}'
        match = re.search(pattern, text)
        
        if match:
            return match.group(0)
        
        return None
    
    def _validate_and_clean(self, data: Dict) -> Dict:
        """
        验证和清洗数据
        
        Args:
            data: 原始数据
            
        Returns:
            清洗后的数据
        """
        result = {
            "score": {
                "total": 0,
                "accuracy": 0,
                "stability": 0,
                "coordination": 0
            },
            "problems": [],
            "suggestions": []
        }
        
        # 处理分数
        if "score" in data and isinstance(data["score"], dict):
            score = data["score"]
            
            # 确保各项分数是整数
            for key in ["total", "accuracy", "stability", "coordination"]:
                if key in score:
                    try:
                        result["score"][key] = int(float(score[key]))
                    except (ValueError, TypeError):
                        result["score"][key] = 0
        
        # 处理问题列表
        if "problems" in data:
            problems = data["problems"]
            if isinstance(problems, list):
                result["problems"] = [str(p) for p in problems if p]
        
        # 处理建议列表
        if "suggestions" in data:
            suggestions = data["suggestions"]
            if isinstance(suggestions, list):
                result["suggestions"] = [str(s) for s in suggestions if s]
        
        # 确保问题和建议至少有2条,不足则补充
        while len(result["problems"]) < 2:
            result["problems"].append("需要更多信息来分析")
        
        while len(result["suggestions"]) < 2:
            result["suggestions"].append("建议咨询专业瑜伽教练")
        
        # 限制问题和建议不超过3条
        result["problems"] = result["problems"][:3]
        result["suggestions"] = result["suggestions"][:3]
        
        # 计算总分(如果总分不等于各项之和)
        manual_total = (result["score"]["accuracy"] + 
                      result["score"]["stability"] + 
                      result["score"]["coordination"])
        
        if result["score"]["total"] != manual_total:
            result["score"]["total"] = manual_total
        
        return result
    
    def _parse_from_text(self, text: str) -> Dict:
        """
        从文本中解析评分和信息
        
        Args:
            text: 原始文本
            
        Returns:
            解析结果
        """
        result = {
            "success": False,
            "error": "无法找到JSON格式的结果",
            "data": {
                "score": {
                    "total": 60,
                    "accuracy": 20,
                    "stability": 20,
                    "coordination": 20
                },
                "problems": [
                    "无法解析详细问题,请检查模型输出"
                ],
                "suggestions": [
                    "建议重新生成评估结果"
                ]
            },
            "raw": text
        }
        
        # 尝试从文本中提取分数
        total_score = self._extract_score(text, "总分")
        if total_score:
            result["data"]["score"]["total"] = total_score
        
        return result
    
    def _extract_score(self, text: str, keyword: str) -> Optional[int]:
        """从文本中提取分数"""
        # 查找"总分: XX"或类似模式
        pattern = rf'{keyword}[:\s]*(\d+)'
        match = re.search(pattern, text)
        
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        return None
    
    def format_result(self, result: Dict) -> str:
        """
        格式化结果以便显示
        
        Args:
            result: 解析后的结果
            
        Returns:
            格式化的字符串
        """
        if not result["success"]:
            return f"解析失败: {result.get('error', '未知错误')}"
        
        data = result["data"]
        score = data["score"]
        
        lines = [
            f"总分: {score['total']}/100",
            f"  - 角度准确性: {score['accuracy']}/40",
            f"  - 动作稳定性: {score['stability']}/30",
            f"  - 整体协调性: {score['coordination']}/30",
            "",
            "主要问题:",
        ]
        
        for i, problem in enumerate(data["problems"], 1):
            lines.append(f"  {i}. {problem}")
        
        lines.append("")
        lines.append("改进建议:")
        
        for i, suggestion in enumerate(data["suggestions"], 1):
            lines.append(f"  {i}. {suggestion}")
        
        return "\n".join(lines)
    
    def get_score_breakdown(self, result: Dict) -> Tuple[int, int, int, int]:
        """
        获取分数分解
        
        Args:
            result: 解析后的结果
            
        Returns:
            (total, accuracy, stability, coordination)
        """
        if result["success"]:
            score = result["data"]["score"]
            return (
                score["total"],
                score["accuracy"],
                score["stability"],
                score["coordination"]
            )
        else:
            return (0, 0, 0, 0)
    
    def get_problems_and_suggestions(self, result: Dict) -> Tuple[List[str], List[str]]:
        """
        获取问题和建议
        
        Args:
            result: 解析后的结果
            
        Returns:
            (problems, suggestions)
        """
        if result["success"]:
            return (
                result["data"]["problems"],
                result["data"]["suggestions"]
            )
        else:
            return ([], [])
