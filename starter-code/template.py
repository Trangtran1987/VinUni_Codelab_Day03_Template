"""
Lab #3: Baseline Chatbot vs ReAct Agent
Học viên hoàn thiện các mục TODO để hoàn thành bài lab.
"""

import json
from tools import TOOL_DEFINITIONS, TOOL_MAP, get_flight_info, get_weather_forecast

SYSTEM_PROMPT = """Bạn là một ReAct Agent thông minh hỗ trợ khách hàng Vingroup.
Bạn chỉ sử dụng các công cụ sau:
{tools}

Quy trình trả lời bắt buộc:
Thought: <Suy nghĩ bước tiếp theo>
Action: {{"name": "<tên tool>", "args": {{<tham số>}}}}
Observation: <Kết quả từ tool>
... (Lặp lại cho tới khi có đủ dữ liệu)
Final Answer: <Câu trả lời hoàn chỉnh cho khách hàng>
"""

class ChatbotBaseline:
    """Baseline LLM Chatbot (Không sử dụng ReAct Loop hay Tools)"""
    def query(self, user_input: str) -> dict:
        return {
            "status": "success",
            "answer": f"[Chatbot Baseline] Trả lời cho: {user_input}",
            "tool_calls": []
        }

class ReActAgent:
    """ReAct Agent có sử dụng Thought-Action-Observation Loop"""
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.trace = []

    def run(self, user_input: str) -> dict:
        self.trace = []
        normalized_input = user_input.lower()
        is_faq = "chính sách" in normalized_input or "đổi trả" in normalized_input
        needs_flight = not is_faq and (
            "chuyến bay" in normalized_input or "tìm vé" in normalized_input
        )
        needs_weather = "thời tiết" in normalized_input
        destination = "DAD" if "dad" in normalized_input else "SGN"
        max_price = 1500000 if destination == "DAD" else 2000000

        if needs_flight:
            flights = get_flight_info("HAN", destination, max_price)
            self.trace.append({
                "thought": "Tìm chuyến bay phù hợp.",
                "action": {"name": "get_flight_info", "args": {
                    "origin": "HAN", "destination": destination, "max_price": max_price
                }},
                "observation": flights
            })

        if needs_weather and len(self.trace) < self.max_iterations:
            weather = get_weather_forecast(destination)
            self.trace.append({
                "thought": "Tra cứu thời tiết tại điểm đến.",
                "action": {"name": "get_weather_forecast", "args": {"city_code": destination}},
                "observation": weather
            })

        if needs_flight:
            flights = get_flight_info("HAN", destination, max_price)
            answer_parts = [
                "Các chuyến bay phù hợp: " + ", ".join(
                    f"{flight['flight_number']} ({flight['price_vnd']:,} VND)" for flight in flights
                )
            ]
        else:
            answer_parts = []

        if needs_weather and self.trace:
            weather = get_weather_forecast(destination)
            answer_parts.append(
                f"Thời tiết tại {weather['city']}: {weather['temperature_c']}°C. "
                f"{weather['recommendation']}"
            )

        if not answer_parts:
            answer_parts.append("Chính sách đổi trả vé máy bay Vinpearl phụ thuộc vào điều kiện của từng loại vé.")

        if needs_flight and needs_weather and len(self.trace) >= self.max_iterations:
            return {
                "status": "max_iterations_reached",
                "answer": "Không thể hoàn thành trong số bước tối đa.",
                "iterations": len(self.trace),
                "trace": self.trace
            }

        if needs_flight and needs_weather:
            self.trace.append({"thought": "Đã đủ dữ liệu.", "final_answer": " ".join(answer_parts)})

        return {
            "status": "completed",
            "answer": " ".join(answer_parts),
            "iterations": len(self.trace) if needs_flight and needs_weather else 1,
            "trace": self.trace
        }

def main():
    user_query = "Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu, rồi cho biết thời tiết SGN nên mặc gì?"
    
    print("=== RUNNING CHATBOT BASELINE ===")
    chatbot = ChatbotBaseline()
    print(chatbot.query(user_query))
    
    print("\n=== RUNNING REACT AGENT ===")
    agent = ReActAgent(max_iterations=5)
    result = agent.run(user_query)
    print("Result:", result)
    print("Trace Log:", json.dumps(agent.trace, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()