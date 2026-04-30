# services/parser_service.py
import json
import re
from typing import Optional, Any
from loguru import logger

class ParserService:
    @staticmethod
    def parse_quiz_from_text(text: str) -> Optional[list[dict]]:
        """Parse quiz questions from plain text format"""
        questions = []
        lines = text.strip().split("\n")
        current_q = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match question number pattern: "1." or "1)" or "Question 1:"
            q_match = re.match(r'^(?:Question\s*)?(\d+)[\.\):]\s*(.+)$', line, re.IGNORECASE)
            if q_match:
                if current_q and len(current_q.get("options", [])) == 4:
                    questions.append(current_q)
                current_q = {
                    "question_text": q_match.group(2),
                    "options": [],
                    "correct_answer": None,
                    "explanation": None,
                    "marks": 1.0,
                }
                continue
            
            # Match option pattern: "A)" or "A." or "A "
            opt_match = re.match(r'^([A-D])[\.\)\s]\s*(.+)$', line)
            if opt_match and current_q:
                current_q["options"].append(opt_match.group(2))
                continue
            
            # Match correct answer: "Answer: A" or "Correct: B"
            ans_match = re.match(r'^(?:Answer|Correct|Ans)[:\s]*([A-D])$', line, re.IGNORECASE)
            if ans_match and current_q:
                current_q["correct_answer"] = ans_match.group(1).upper()
                continue
            
            # Match explanation
            exp_match = re.match(r'^(?:Explanation|Exp|Reason)[:\s]*(.+)$', line, re.IGNORECASE)
            if exp_match and current_q:
                current_q["explanation"] = exp_match.group(1)
                continue
            
            # Match marks
            marks_match = re.match(r'^Marks?[:\s]*(\d+\.?\d*)$', line, re.IGNORECASE)
            if marks_match and current_q:
                current_q["marks"] = float(marks_match.group(1))
        
        # Save last question
        if current_q and len(current_q.get("options", [])) == 4:
            questions.append(current_q)
        
        if questions:
            logger.info("Parsed {} questions from text", len(questions))
        return questions if questions else None

    @staticmethod
    def parse_bulk_upload(text: str) -> Optional[dict]:
        """Parse bulk upload format — JSON or structured text"""
        text = text.strip()
        
        # Try JSON first
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return {"quizzes": [{"title": "Uploaded Quiz", "questions": data}]}
            if isinstance(data, dict) and "questions" in data:
                return {"quizzes": [data]}
            if isinstance(data, dict) and "quizzes" in data:
                return data
        except json.JSONDecodeError:
            pass
        
        # Try structured text
        questions = ParserService.parse_quiz_from_text(text)
        if questions:
            return {"quizzes": [{"title": "Parsed Quiz", "questions": questions}]}
        
        return None
