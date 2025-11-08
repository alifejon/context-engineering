#!/usr/bin/env python3
"""
Conversation Window Example

멀티턴 대화에서 최근 N턴만 유지하는
슬라이딩 윈도우 기법을 시연합니다.
"""

import sys
import os
from typing import List, Dict

# Add parent directory to path for shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    print_section,
    print_success,
    print_warning
)


class ConversationWindow:
    """대화 윈도우 관리자"""

    def __init__(self, max_turns: int = 5, max_tokens: int = 4000, model: str = "gpt-4"):
        """
        Args:
            max_turns: 최대 유지할 턴 수
            max_tokens: 최대 토큰 수
            model: 토큰화 모델
        """
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.model = model
        self.system_prompt = None
        self.messages = []

    def set_system_prompt(self, prompt: str):
        """시스템 프롬프트 설정 (항상 유지됨)"""
        self.system_prompt = {
            "role": "system",
            "content": prompt
        }

    def add_message(self, role: str, content: str) -> Dict:
        """
        메시지 추가 및 윈도우 관리

        Args:
            role: "user" 또는 "assistant"
            content: 메시지 내용

        Returns:
            윈도우 상태
        """
        message = {"role": role, "content": content}
        self.messages.append(message)

        # 윈도우 크기 체크
        self._manage_window()

        return self.get_window_status()

    def _manage_window(self):
        """윈도우 크기 관리"""
        # 1. 턴 수 제한
        while len(self.messages) > self.max_turns * 2:  # user + assistant = 1 turn
            removed = self.messages.pop(0)
            print(f"  🗑️  Removed old message: {removed['role']} ({len(removed['content'])} chars)")

        # 2. 토큰 수 제한
        total_tokens = self._count_total_tokens()
        while total_tokens > self.max_tokens and len(self.messages) > 2:
            removed = self.messages.pop(0)
            print(f"  🗑️  Removed to fit token budget: {removed['role']}")
            total_tokens = self._count_total_tokens()

    def _count_total_tokens(self) -> int:
        """전체 토큰 수 계산"""
        total = 0

        if self.system_prompt:
            total += count_tokens(self.system_prompt["content"], self.model)

        for msg in self.messages:
            total += count_tokens(msg["content"], self.model)
            total += 4  # Message overhead

        return total

    def get_messages_for_api(self) -> List[Dict]:
        """API 호출용 메시지 목록"""
        if self.system_prompt:
            return [self.system_prompt] + self.messages
        return self.messages

    def get_window_status(self) -> Dict:
        """윈도우 상태 조회"""
        total_tokens = self._count_total_tokens()
        num_turns = len(self.messages) // 2

        return {
            "num_messages": len(self.messages),
            "num_turns": num_turns,
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": total_tokens / self.max_tokens,
            "can_add_more": total_tokens < self.max_tokens * 0.9
        }

    def print_status(self):
        """상태 출력"""
        status = self.get_window_status()

        print(f"\n{'='*60}")
        print(f"Window Status:")
        print(f"  Messages: {status['num_messages']} ({status['num_turns']} turns)")
        print(f"  Tokens: {format_tokens(status['total_tokens'])} / {format_tokens(status['max_tokens'])}")
        print(f"  Utilization: {status['utilization']:.1%}")

        if status['utilization'] > 0.9:
            print_warning("  ⚠ Window nearly full!")
        elif status['utilization'] > 0.7:
            print(f"  ⚠ Warning: {status['utilization']:.1%} full")
        else:
            print(f"  ✓ Healthy")

        print(f"{'='*60}\n")


def simulate_conversation():
    """대화 시뮬레이션"""
    print_section("CONVERSATION WINDOW SIMULATION")

    # 윈도우 생성
    window = ConversationWindow(max_turns=5, max_tokens=2000)

    # 시스템 프롬프트 설정
    system_prompt = "You are a helpful AI assistant. Be concise but informative."
    window.set_system_prompt(system_prompt)

    print(f"Configuration:")
    print(f"  Max turns: {window.max_turns}")
    print(f"  Max tokens: {format_tokens(window.max_tokens)}")
    print(f"  System prompt: {count_tokens(system_prompt)} tokens\n")

    # 시뮬레이션 대화
    conversations = [
        ("Hello!", "Hi! How can I help you today?"),
        ("What is context engineering?", "Context engineering is a systematic approach to managing LLM context windows efficiently."),
        ("How does it differ from prompt engineering?", "While prompt engineering focuses on what to ask, context engineering focuses on how to manage the information provided."),
        ("Can you give me an example?", "Sure! For instance, context compression reduces token count while preserving meaning. This can cut costs by 60-80%."),
        ("What about RAG?", "RAG retrieves external knowledge. Context engineering optimizes how that knowledge is presented to the LLM."),
        ("Tell me more about compression", "Context compression uses techniques like extractive summarization, semantic deduplication, and hybrid approaches."),
        ("What's the best strategy?", "It depends on your use case. For production, hybrid compression with priority-based selection works well."),
    ]

    for i, (user_msg, assistant_msg) in enumerate(conversations, 1):
        print(f"\n{'─'*60}")
        print(f"Turn {i}:")
        print(f"{'─'*60}")

        # User message
        print(f"👤 User: {user_msg}")
        status = window.add_message("user", user_msg)

        # Assistant message
        print(f"🤖 Assistant: {assistant_msg}")
        status = window.add_message("assistant", assistant_msg)

        # Status
        print(f"\n📊 After Turn {i}:")
        print(f"   Messages in window: {status['num_messages']} (turns: {status['num_turns']})")
        print(f"   Tokens: {format_tokens(status['total_tokens'])} ({status['utilization']:.1%})")

        if not status['can_add_more']:
            print_warning("   ⚠ Window getting full, old messages will be removed")

    # Final status
    window.print_status()

    # Show what would be sent to API
    print_section("MESSAGES FOR API CALL")

    messages = window.get_messages_for_api()
    for i, msg in enumerate(messages):
        role_emoji = "⚙️" if msg["role"] == "system" else "👤" if msg["role"] == "user" else "🤖"
        preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
        tokens = count_tokens(msg["content"])
        print(f"{i+1}. {role_emoji} {msg['role']:10} [{tokens:4} tokens] {preview}")

    print_success("\nSimulation complete!")


def main():
    simulate_conversation()

    print("\n💡 Key Takeaways:")
    print("  1. Sliding window keeps only recent N turns")
    print("  2. System prompt is always preserved")
    print("  3. Old messages are removed when limits are reached")
    print("  4. Monitor token usage to prevent sudden cuts")


if __name__ == "__main__":
    main()
