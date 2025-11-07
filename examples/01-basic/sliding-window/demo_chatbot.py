#!/usr/bin/env python3
"""
Interactive Chatbot Demo

실제 챗봇에서 슬라이딩 윈도우를 적용한
인터랙티브 데모입니다.

Note: OpenAI API 키가 있으면 실제 LLM과 대화,
      없으면 시뮬레이션 모드로 동작합니다.
"""

import sys
import os

# Add parent directory to path for shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    load_api_key,
    print_section,
    print_success,
    print_warning,
    print_error
)
from conversation_window import ConversationWindow


class ChatBot:
    """슬라이딩 윈도우를 사용하는 챗봇"""

    def __init__(self, max_turns: int = 5, max_tokens: int = 4000, use_real_llm: bool = False):
        self.window = ConversationWindow(max_turns=max_turns, max_tokens=max_tokens)
        self.use_real_llm = use_real_llm
        self.client = None

        # 시스템 프롬프트 설정
        system_prompt = """You are a helpful AI assistant that explains context engineering concepts.
Be concise but informative. Use examples when helpful."""
        self.window.set_system_prompt(system_prompt)

        # OpenAI 클라이언트 설정 (옵션)
        if use_real_llm:
            api_key = load_api_key("openai")
            if api_key:
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=api_key)
                    print_success("✓ Connected to OpenAI API")
                except ImportError:
                    print_error("✗ OpenAI package not installed")
                    print("  Run: pip install openai")
                    self.use_real_llm = False
            else:
                print_warning("⚠ No OpenAI API key found, using simulation mode")
                self.use_real_llm = False

    def get_response(self, user_message: str) -> str:
        """응답 생성"""
        # 사용자 메시지 추가
        self.window.add_message("user", user_message)

        if self.use_real_llm and self.client:
            # 실제 LLM 호출
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=self.window.get_messages_for_api(),
                    max_tokens=500,
                    temperature=0.7
                )
                assistant_message = response.choices[0].message.content
            except Exception as e:
                assistant_message = f"Error: {str(e)}"
        else:
            # 시뮬레이션 응답
            assistant_message = self._simulate_response(user_message)

        # 어시스턴트 메시지 추가
        self.window.add_message("assistant", assistant_message)

        return assistant_message

    def _simulate_response(self, user_message: str) -> str:
        """시뮬레이션 응답 생성"""
        responses = {
            "hello": "Hello! I'm here to help you learn about context engineering. What would you like to know?",
            "context": "Context engineering is about efficiently managing LLM context windows through techniques like compression, prioritization, and dynamic assembly.",
            "prompt": "While prompt engineering focuses on what to ask, context engineering focuses on how to manage the information provided to the LLM.",
            "rag": "RAG retrieves external knowledge, and context engineering optimizes how that knowledge is presented to reduce tokens and costs.",
            "cost": "Context engineering can reduce costs by 60-80% through compression and smart token management.",
            "example": "For example, instead of sending 10 full documents (20K tokens), you can compress to 5K tokens while preserving key information.",
        }

        # Simple keyword matching
        user_lower = user_message.lower()
        for keyword, response in responses.items():
            if keyword in user_lower:
                return response

        return "That's an interesting question! Context engineering involves managing LLM inputs efficiently. Would you like to know more about compression, prioritization, or cost optimization?"

    def print_status(self):
        """상태 출력"""
        self.window.print_status()

    def run_interactive(self):
        """인터랙티브 모드 실행"""
        print_section("INTERACTIVE CHATBOT DEMO")

        mode = "Real LLM" if self.use_real_llm else "Simulation"
        print(f"Mode: {mode}")
        print(f"Max turns: {self.window.max_turns}")
        print(f"Max tokens: {format_tokens(self.window.max_tokens)}\n")

        print("Commands:")
        print("  /status - Show window status")
        print("  /history - Show conversation history")
        print("  /quit - Exit")
        print("\nStart chatting!\n")

        turn = 0

        while True:
            turn += 1

            # Get user input
            try:
                user_input = input(f"\n[Turn {turn}] You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nGoodbye!")
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith('/'):
                if user_input == '/quit':
                    print("\nGoodbye!")
                    break
                elif user_input == '/status':
                    self.print_status()
                    turn -= 1
                    continue
                elif user_input == '/history':
                    self._print_history()
                    turn -= 1
                    continue
                else:
                    print(f"Unknown command: {user_input}")
                    turn -= 1
                    continue

            # Get response
            response = self.get_response(user_input)

            # Print response
            print(f"Bot: {response}")

            # Show token usage
            status = self.window.get_window_status()
            print(f"\n[Tokens: {format_tokens(status['total_tokens'])} / {format_tokens(status['max_tokens'])} ({status['utilization']:.1%})]")

            if status['utilization'] > 0.8:
                print_warning("⚠ Window is getting full. Old messages will be removed soon.")

    def _print_history(self):
        """대화 히스토리 출력"""
        print("\n" + "="*60)
        print("CONVERSATION HISTORY")
        print("="*60 + "\n")

        messages = self.window.get_messages_for_api()

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            tokens = count_tokens(content)

            if role == "system":
                print(f"⚙️  System [{tokens} tokens]:")
                print(f"    {content[:80]}...")
            elif role == "user":
                print(f"\n👤 User [{tokens} tokens]:")
                print(f"    {content}")
            else:
                print(f"🤖 Assistant [{tokens} tokens]:")
                print(f"    {content}")

        print("\n" + "="*60 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Interactive chatbot demo")
    parser.add_argument("--real-llm", action="store_true", help="Use real LLM (requires API key)")
    parser.add_argument("--max-turns", type=int, default=5, help="Maximum turns to keep")
    parser.add_argument("--max-tokens", type=int, default=4000, help="Maximum tokens")
    parser.add_argument("--demo", action="store_true", help="Run automated demo instead of interactive")

    args = parser.parse_args()

    # Create chatbot
    bot = ChatBot(
        max_turns=args.max_turns,
        max_tokens=args.max_tokens,
        use_real_llm=args.real_llm
    )

    if args.demo:
        # Automated demo
        print_section("AUTOMATED DEMO")

        demo_messages = [
            "Hello!",
            "What is context engineering?",
            "How is it different from prompt engineering?",
            "Can you give me an example?",
            "What about costs?",
            "Tell me more about compression techniques",
        ]

        for i, msg in enumerate(demo_messages, 1):
            print(f"\n{'─'*60}")
            print(f"Turn {i}")
            print(f"{'─'*60}")
            print(f"👤 You: {msg}")

            response = bot.get_response(msg)
            print(f"🤖 Bot: {response}")

            status = bot.window.get_window_status()
            print(f"\n[Tokens: {format_tokens(status['total_tokens'])} ({status['utilization']:.1%})]")

        bot.print_status()
        print_success("\nDemo complete!")

    else:
        # Interactive mode
        bot.run_interactive()


if __name__ == "__main__":
    main()
