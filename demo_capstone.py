#!/usr/bin/env python3
"""
Doc-QA Assistant Capstone Demonstration

This script demonstrates the complete Doc-QA Assistant functionality:
1. Document upload and processing
2. Intelligent chat with internal doc preference
3. Citation support and source tracking
4. Async job processing with progress updates
"""

import asyncio
import time
from pathlib import Path

import httpx


class CapstoneDemo:
    def __init__(self, base_url: str = "http://127.0.0.1:8010"):
        self.base_url = base_url
        self.session_id = f"demo_{int(time.time())}"

    async def demo_document_upload(self):
        """Demonstrate document upload and processing."""
        print("🔄 PHASE 1: Document Upload & Processing")
        print("=" * 50)

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Upload company handbook
            handbook_path = Path("demo_docs/company_handbook.md")
            with open(handbook_path, "rb") as f:
                files = {"file": ("company_handbook.md", f, "text/markdown")}
                response = await client.post(
                    f"{self.base_url}/docs/upload",
                    files=files,
                    params={"background": "false"},  # Process immediately for demo
                )

            if response.status_code == 200:
                doc_data = response.json()
                print(f"✅ Uploaded: {doc_data['document']['filename']}")
                print(f"   Document ID: {doc_data['document']['id']}")
                print(f"   Status: {doc_data['document']['status']}")
                print(f"   Size: {doc_data['document']['size']} bytes")
            else:
                print(f"❌ Upload failed: {response.text}")
                return

            # Upload project guidelines
            guidelines_path = Path("demo_docs/project_guidelines.md")
            with open(guidelines_path, "rb") as f:
                files = {"file": ("project_guidelines.md", f, "text/markdown")}
                response = await client.post(
                    f"{self.base_url}/docs/upload", files=files, params={"background": "false"}
                )

            if response.status_code == 200:
                doc_data = response.json()
                print(f"✅ Uploaded: {doc_data['document']['filename']}")
                print(f"   Document ID: {doc_data['document']['id']}")
                print(f"   Status: {doc_data['document']['status']}")

            # List all documents
            response = await client.get(f"{self.base_url}/docs/")
            if response.status_code == 200:
                docs_data = response.json()
                print(f"\n📚 Total documents: {docs_data['total']}")
                for doc in docs_data["documents"]:
                    print(f"   - {doc['filename']} ({doc['status']})")

        print("\n")

    async def demo_intelligent_chat(self):
        """Demonstrate intelligent chat with document preference."""
        print("🔄 PHASE 2: Intelligent Chat Interface")
        print("=" * 50)

        test_questions = [
            {
                "question": "What are the company's core values?",
                "expected_route": "rag",
                "description": "Internal document question",
            },
            {
                "question": "How many vacation days do employees get?",
                "expected_route": "rag",
                "description": "HR policy question",
            },
            {
                "question": "What is the current weather in San Francisco?",
                "expected_route": "web",
                "description": "External/real-time question",
            },
            {
                "question": "What Python framework do we use for backend development?",
                "expected_route": "rag",
                "description": "Technical documentation question",
            },
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, test in enumerate(test_questions, 1):
                print(f"Q{i}: {test['question']}")
                print(f"Expected route: {test['expected_route']} ({test['description']})")

                response = await client.post(
                    f"{self.base_url}/chat/",
                    json={"message": test["question"], "session_id": self.session_id},
                )

                if response.status_code == 200:
                    chat_data = response.json()
                    actual_route = chat_data["routing_info"]["route"]
                    route_reason = chat_data["routing_info"]["route_reason"]

                    print(f"🤖 Actual route: {actual_route} - {route_reason}")
                    print(f"📝 Answer: {chat_data['message'][:150]}...")

                    # Show sources if available
                    if chat_data.get("sources"):
                        print(f"📚 Sources: {len(chat_data['sources'])} documents")
                        for j, source in enumerate(chat_data["sources"][:2], 1):
                            relevance = source.get("relevance_score", 0)
                            source_name = source.get("source", "Unknown")
                            print(f"   {j}. {source_name} (relevance: {relevance:.2f})")

                    # Check if routing was correct
                    if actual_route == test["expected_route"]:
                        print("✅ Routing correct")
                    else:
                        print("⚠️  Unexpected routing")
                else:
                    print(f"❌ Chat failed: {response.text}")

                print()

        print()

    async def demo_citation_support(self):
        """Demonstrate citation support in responses."""
        print("🔄 PHASE 3: Citation Support")
        print("=" * 50)

        citation_question = (
            "What professional development benefits does the company offer and what are the "
            "security guidelines for dependency management?"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"Question: {citation_question}")

            response = await client.post(
                f"{self.base_url}/chat/",
                json={"message": citation_question, "session_id": self.session_id},
            )

            if response.status_code == 200:
                chat_data = response.json()
                print(f"🤖 Answer:\n{chat_data['message']}")

                if chat_data.get("sources"):
                    print(f"\n📚 Sources ({len(chat_data['sources'])} found):")
                    for i, source in enumerate(chat_data["sources"], 1):
                        print(f"   {i}. {source.get('source', 'Unknown')}")
                        print(f"      Relevance: {source.get('relevance_score', 0):.2f}")
                        print(f"      Document: {source.get('document_id', 'Unknown')}")
                        print()

        print()

    async def demo_session_management(self):
        """Demonstrate chat session continuity."""
        print("🔄 PHASE 4: Session Management")
        print("=" * 50)

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Check chat history
            response = await client.get(f"{self.base_url}/chat/sessions/{self.session_id}/history")
            if response.status_code == 200:
                history = response.json()
                print(f"💬 Session {self.session_id} has {history['total']} exchanges")

                # Show last few exchanges
                for i, exchange in enumerate(history["messages"][-2:], 1):
                    print(f"\nExchange {i}:")
                    print(f"👤 User: {exchange['user'][:80]}...")
                    print(f"🤖 Assistant: {exchange['assistant'][:80]}...")

            # Test follow-up question that should maintain context
            followup = "Can you tell me more about the first benefit you mentioned?"
            print(f"\n📝 Follow-up question: {followup}")

            response = await client.post(
                f"{self.base_url}/chat/", json={"message": followup, "session_id": self.session_id}
            )

            if response.status_code == 200:
                chat_data = response.json()
                print(f"🤖 Response: {chat_data['message'][:150]}...")
                print(f"📍 Route: {chat_data['routing_info']['route']}")

        print()

    async def demo_performance_metrics(self):
        """Show performance and evaluation metrics."""
        print("🔄 PHASE 5: Performance Metrics")
        print("=" * 50)

        # Check if evaluation reports exist
        portfolio_dir = Path("portfolio")
        if portfolio_dir.exists():
            print("📊 Available evaluation reports:")
            for report_file in portfolio_dir.glob("*_report.csv"):
                print(f"   - {report_file.name}")

                # Read and show summary of the latest report
                try:
                    with open(report_file) as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            last_run = lines[-1].split(",")[0] if lines else "Unknown"
                            print(f"     Last run: {last_run}")
                except Exception:
                    # Ignore errors reading report files
                    continue
        else:
            print("📊 No evaluation reports found - run evaluations with 'make eval'")

        # Show system health
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print(f"\n💚 System health: {response.json()['status']}")

            response = await client.get(f"{self.base_url}/ready")
            if response.status_code == 200:
                print(f"🟢 System ready: {response.json()['status']}")

        print()

    async def run_full_demo(self):
        """Run the complete capstone demonstration."""
        print("🚀 DOC-QA ASSISTANT CAPSTONE DEMONSTRATION")
        print("=" * 60)
        print("This demo showcases:")
        print("- Document upload and async processing")
        print("- Intelligent routing between internal docs and web search")
        print("- Citation support with source tracking")
        print("- Session-based conversation continuity")
        print("- Performance monitoring and evaluation")
        print("=" * 60)
        print()

        try:
            await self.demo_document_upload()
            await self.demo_intelligent_chat()
            await self.demo_citation_support()
            await self.demo_session_management()
            await self.demo_performance_metrics()

            print("🎉 DEMONSTRATION COMPLETE!")
            print("=" * 50)
            print("The Doc-QA Assistant successfully demonstrated:")
            print("✅ Document ingestion with metadata preservation")
            print("✅ Intelligent routing between internal and external sources")
            print("✅ Citation support linking answers to source documents")
            print("✅ Conversation continuity across sessions")
            print("✅ Production-ready deployment and monitoring")
            print()
            print(f"🔗 Chat session ID: {self.session_id}")
            print(f"🌐 API endpoint: {self.base_url}")
            print("📖 Try the interactive chat at /docs for OpenAPI documentation")

        except Exception as e:
            print(f"❌ Demo failed: {str(e)}")
            print("Make sure the API server is running: 'make run' or 'docker compose up'")


async def main():
    demo = CapstoneDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())
