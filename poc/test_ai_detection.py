#!/usr/bin/env python3
"""
AI Structure Detection Test Script

This script tests and compares AI-powered vs regex-based document structure detection.
It provides detailed accuracy metrics, cost analysis, and performance comparisons.

Usage:
    python poc/test_ai_detection.py                    # Test all files
    python poc/test_ai_detection.py --file test_data/sample_short.txt  # Test specific file
    python poc/test_ai_detection.py --verbose         # Detailed output
    python poc/test_ai_detection.py --model gpt-3.5-turbo  # Use different model
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add poc directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from converters import convert, compare_detection_methods
    from idm_schema import IDMDocument
except ImportError:
    print("Error: Could not import required modules. Make sure you're running from the poc directory.")
    sys.exit(1)


class AIDetectionTester:
    """Test harness for AI structure detection"""

    def __init__(self, model: str = "gpt-4-turbo-preview"):
        self.model = model
        self.test_files = [
            'test_data/sample_short.txt',
            'test_data/sample_medium.txt',
            'test_data/sample_nonfiction.txt'
        ]
        # Expected chapter counts for accuracy validation
        self.expected_counts = {
            'test_data/sample_short.txt': {'chapters': 6, 'min_chapters': 4, 'max_chapters': 8},  # Foreword + 5 Letters
            'test_data/sample_medium.txt': {'chapters': 5, 'min_chapters': 3, 'max_chapters': 7},  # Intro + 4 chapters
            'test_data/sample_nonfiction.txt': {'chapters': 5, 'min_chapters': 4, 'max_chapters': 6}  # Intro + 3 chapters + Conclusion
        }
        self.results = []

    def check_environment(self) -> bool:
        """Check if environment is ready for AI testing"""
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY environment variable not set")
            print("   Please set your OpenAI API key:")
            print("   export OPENAI_API_KEY=your-key-here")
            return False
        return True

    def run_detection_test(self, file_path: str, use_ai: bool) -> Dict[str, Any]:
        """Run a single detection test and return results"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        start_time = time.time()
        try:
            document = convert(file_path, use_ai=use_ai, ai_model=self.model)
            processing_time = time.time() - start_time

            # Calculate word count
            word_count = sum(len(chapter.paragraphs) * 10 for chapter in document.chapters)  # Rough estimate

            chapters_detected = len(document.chapters)

            # Calculate accuracy metrics if expected counts are available
            expected = self.expected_counts.get(file_path, {})
            accuracy_score = None
            within_tolerance = None

            if expected:
                expected_chapters = expected['chapters']
                min_chapters = expected.get('min_chapters', expected_chapters - 1)
                max_chapters = expected.get('max_chapters', expected_chapters + 1)

                # Simple accuracy scoring (closer to expected = higher score)
                if chapters_detected == expected_chapters:
                    accuracy_score = 100
                elif min_chapters <= chapters_detected <= max_chapters:
                    accuracy_score = 75  # Within tolerance
                else:
                    accuracy_score = max(0, 100 - abs(chapters_detected - expected_chapters) * 10)

                within_tolerance = min_chapters <= chapters_detected <= max_chapters

            result = {
                "file": file_path,
                "method": "ai" if use_ai else "regex",
                "success": True,
                "chapters_detected": chapters_detected,
                "expected_chapters": expected.get('chapters') if expected else None,
                "accuracy_score": accuracy_score,
                "within_tolerance": within_tolerance,
                "blocks_detected": sum(len(chapter.blocks) if hasattr(chapter, 'blocks') else len(chapter.paragraphs) for chapter in document.chapters),
                "word_count": document.metadata.word_count,
                "processing_time": round(processing_time, 2),
                "ai_cost": document.metadata.ai_cost if use_ai else 0.0,
                "has_front_matter": document.metadata.has_front_matter,
                "has_back_matter": document.metadata.has_back_matter,
                "detected_by_ai": document.metadata.detected_by_ai
            }

        except Exception as e:
            processing_time = time.time() - start_time
            result = {
                "file": file_path,
                "method": "ai" if use_ai else "regex",
                "success": False,
                "error": str(e),
                "processing_time": round(processing_time, 2)
            }

        return result

    def compare_detections(self, file_path: str) -> Dict[str, Any]:
        """Compare regex vs AI detection for a file"""
        print(f"\n🔍 Comparing detection methods for: {file_path}")

        comparison = compare_detection_methods(file_path)
        return comparison

    def generate_report(self, results: List[Dict[str, Any]], output_file: str = "docs/ai_detection_test_results.md"):
        """Generate a comprehensive test report"""
        print(f"\n📊 Generating test report: {output_file}")

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AI Structure Detection Test Results\n\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Model Used:** {self.model}\n\n")

            # Summary statistics
            total_tests = len(results)
            successful_tests = len([r for r in results if r.get("success", False)])
            ai_tests = [r for r in results if r.get("method") == "ai" and r.get("success")]
            regex_tests = [r for r in results if r.get("method") == "regex" and r.get("success")]

            total_ai_cost = sum(r.get("ai_cost", 0) for r in ai_tests)
            total_processing_time = sum(r.get("processing_time", 0) for r in results)

            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Tests:** {total_tests}\n")
            f.write(f"- **Successful Tests:** {successful_tests}\n")
            f.write(f"- **AI Tests:** {len(ai_tests)}\n")
            f.write(f"- **Regex Tests:** {len(regex_tests)}\n")
            f.write(f"- **Total AI Cost:** ${total_ai_cost:.4f}\n")
            f.write(f"- **Total Processing Time:** {total_processing_time:.2f}s\n\n")

            # Accuracy metrics for AI tests
            ai_accuracy_scores = [r.get("accuracy_score", 0) for r in ai_tests if r.get("accuracy_score") is not None]
            avg_accuracy = sum(ai_accuracy_scores) / len(ai_accuracy_scores) if ai_accuracy_scores else 0
            within_tolerance_count = sum(1 for r in ai_tests if r.get("within_tolerance"))

            f.write("## Accuracy Metrics\n\n")
            f.write(f"- **Average AI Accuracy:** {avg_accuracy:.1f}%\n")
            f.write(f"- **Tests Within Tolerance:** {within_tolerance_count}/{len(ai_tests)} ({within_tolerance_count/len(ai_tests)*100:.1f}%)\n\n")

            # Detailed results table
            f.write("## Detailed Results\n\n")
            f.write("| File | Method | Chapters | Expected | Accuracy | Within Tol | Blocks | Words | Time | Cost | Status |\n")
            f.write("|------|--------|----------|----------|----------|------------|--------|-------|------|------|--------|\n")

            for result in sorted(results, key=lambda x: (x["file"], x["method"])):
                status = "✅" if result.get("success") else "❌"
                chapters = result.get("chapters_detected", "-")
                expected = result.get("expected_chapters", "-")
                accuracy = f"{result.get('accuracy_score', '-')}%"
                tolerance = "✅" if result.get("within_tolerance") else ("-" if result.get("expected_chapters") is None else "❌")
                blocks = result.get("blocks_detected", "-")
                words = result.get("word_count", "-")
                proc_time = result.get("processing_time", "-")
                cost = f"${result.get('ai_cost', 0):.4f}" if result.get("method") == "ai" else "$0.00"
                method = result["method"].upper()

                f.write(f"| {result['file']} | {method} | {chapters} | {expected} | {accuracy} | {tolerance} | {blocks} | {words} | {proc_time}s | {cost} | {status} |\n")

            f.write("\n## Cost Analysis\n\n")

            if ai_tests:
                avg_cost_per_test = total_ai_cost / len(ai_tests)
                avg_cost_per_word = total_ai_cost / sum(r.get("word_count", 1) for r in ai_tests) * 1000  # per 1k words

                f.write(f"- **Average cost per AI test:** ${avg_cost_per_test:.4f}\n")
                f.write(f"- **Average cost per 1,000 words:** ${avg_cost_per_word:.4f}\n")
                f.write(f"- **Total AI API calls:** {len(ai_tests)}\n\n")

                f.write("### Cost Breakdown by File Size\n\n")
                small_files = [r for r in ai_tests if r.get("word_count", 0) < 5000]
                medium_files = [r for r in ai_tests if 5000 <= r.get("word_count", 0) < 20000]
                large_files = [r for r in ai_tests if r.get("word_count", 0) >= 20000]

                if small_files:
                    avg_small = sum(r.get("ai_cost", 0) for r in small_files) / len(small_files)
                    f.write(f"- **Small files (< 5k words):** ${avg_small:.4f} average\n")
                if medium_files:
                    avg_medium = sum(r.get("ai_cost", 0) for r in medium_files) / len(medium_files)
                    f.write(f"- **Medium files (5k-20k words):** ${avg_medium:.4f} average\n")
                if large_files:
                    avg_large = sum(r.get("ai_cost", 0) for r in large_files) / len(large_files)
                    f.write(f"- **Large files (20k+ words):** ${avg_large:.4f} average\n")

            f.write("\n## Performance Analysis\n\n")

            if ai_tests and regex_tests:
                ai_times = [r["processing_time"] for r in ai_tests]
                regex_times = [r["processing_time"] for r in regex_tests]

                avg_ai_time = sum(ai_times) / len(ai_times)
                avg_regex_time = sum(regex_times) / len(regex_times)

                f.write(f"- **Average AI processing time:** {avg_ai_time:.2f}s\n")
                f.write(f"- **Average regex processing time:** {avg_regex_time:.2f}s\n")
                f.write(f"- **AI overhead:** {avg_ai_time - avg_regex_time:.2f}s ({((avg_ai_time / avg_regex_time - 1) * 100):.1f}% slower)\n\n")

            f.write("## Recommendations\n\n")

            if ai_tests:
                # Analyze if AI improved detection
                improvements = 0
                for ai_result in ai_tests:
                    file_path = ai_result["file"]
                    regex_result = next((r for r in regex_tests if r["file"] == file_path), None)
                    if regex_result and ai_result["chapters_detected"] > regex_result["chapters_detected"]:
                        improvements += 1

                improvement_rate = improvements / len(ai_tests) * 100
                f.write(f"- **AI improved chapter detection in {improvement_rate:.1f}% of tests**\n")

                if total_ai_cost > 0:
                    f.write("- **Cost-effective for:** Documents where accurate structure detection is critical\n")
                    f.write("- **Consider regex for:** Simple documents or when budget is constrained\n")

            f.write("\n## Test Configuration\n\n")
            f.write(f"- **OpenAI Model:** {self.model}\n")
            f.write("- **Chunk Size:** 2000 characters\n")
            f.write("- **Temperature:** 0 (deterministic)\n")
            f.write("- **Response Format:** JSON mode\n")

        print(f"✅ Report saved to: {output_file}")

    def run_all_tests(self, verbose: bool = False) -> List[Dict[str, Any]]:
        """Run comprehensive test suite"""
        print("🚀 Starting AI Detection Test Suite")
        print(f"Model: {self.model}")

        if not self.check_environment():
            return []

        all_results = []

        # Test each file with both methods
        for file_path in self.test_files:
            if not os.path.exists(file_path):
                print(f"⚠️  Skipping {file_path} (file not found)")
                continue

            # Test regex method
            print(f"📄 Testing {file_path} with regex detection...")
            regex_result = self.run_detection_test(file_path, use_ai=False)
            all_results.append(regex_result)

            if verbose:
                if regex_result.get("success"):
                    print(f"   ✅ Regex: {regex_result['chapters_detected']} chapters, {regex_result['processing_time']}s")
                else:
                    print(f"   ❌ Regex failed: {regex_result.get('error')}")

            # Test AI method
            print(f"🤖 Testing {file_path} with AI detection...")
            ai_result = self.run_detection_test(file_path, use_ai=True)
            all_results.append(ai_result)

            if verbose:
                if ai_result.get("success"):
                    print(f"   ✅ AI: {ai_result['chapters_detected']} chapters, ${ai_result['ai_cost']:.4f}, {ai_result['processing_time']}s")
                else:
                    print(f"   ❌ AI failed: {ai_result.get('error')}")

        return all_results


def main():
    parser = argparse.ArgumentParser(description='AI Structure Detection Tester')
    parser.add_argument('--file', '-f', help='Test specific file only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--model', '-m', default='gpt-4-turbo-preview',
                       choices=['gpt-4-turbo-preview', 'gpt-3.5-turbo'],
                       help='OpenAI model to use')
    parser.add_argument('--output', '-o', default='docs/ai_detection_test_results.md',
                       help='Output file for test results')

    args = parser.parse_args()

    tester = AIDetectionTester(model=args.model)

    if args.file:
        # Test specific file
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)

        comparison = tester.compare_detections(args.file)
        print("\n=== Comparison Results ===")
        print(json.dumps(comparison, indent=2))

    else:
        # Run full test suite
        results = tester.run_all_tests(verbose=args.verbose)

        if results:
            tester.generate_report(results, args.output)

            # Print summary to console
            successful = len([r for r in results if r.get("success")])
            ai_cost = sum(r.get("ai_cost", 0) for r in results if r.get("method") == "ai")

            print("\n🎯 Test Summary:")
            print(f"   Tests run: {len(results)}")
            print(f"   Successful: {successful}")
            print(f"   Total AI cost: ${ai_cost:.4f}")
            print(f"   Full report: {args.output}")
        else:
            print("❌ No tests were run. Check your environment setup.")


if __name__ == '__main__':
    main()
