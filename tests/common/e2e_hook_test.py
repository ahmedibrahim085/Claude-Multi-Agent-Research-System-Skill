#!/usr/bin/env python3
"""
Comprehensive E2E Test Suite for user-prompt-submit.py hook

Tests all keywords, patterns, edge cases, and potential regressions.
Run with: python3 tests/common/e2e_hook_test.py
"""

import subprocess
import json
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

HOOK_PATH = Path(__file__).parent.parent.parent / '.claude' / 'hooks' / 'user-prompt-submit.py'

def run_hook(prompt: str) -> dict:
    """Run the hook with a given prompt and return parsed result."""
    try:
        proc = subprocess.run(
            ['python3', str(HOOK_PATH)],
            input=json.dumps({"user_prompt": prompt}),
            capture_output=True,
            text=True,
            timeout=5
        )
        if proc.stdout.strip():
            return json.loads(proc.stdout)
        return {"systemMessage": ""}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON output", "raw": proc.stdout}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)}


def check_triggers(result: dict, expected_skill: str = None, expected_compound: bool = False) -> tuple:
    """
    Check if result matches expected behavior.
    Returns (passed: bool, reason: str)
    """
    msg = result.get('systemMessage', '')

    if 'error' in result:
        return False, f"Error: {result['error']}"

    if expected_compound:
        if 'COMPOUND REQUEST' in msg:
            return True, "Compound detected"
        return False, "Expected COMPOUND REQUEST"

    if expected_skill == 'research':
        if 'RESEARCH WORKFLOW' in msg and 'COMPOUND' not in msg:
            return True, "Research triggered"
        if 'COMPOUND' in msg:
            return False, "Got COMPOUND instead of research-only"
        return False, "Research not triggered"

    if expected_skill == 'planning':
        if 'PLANNING WORKFLOW' in msg and 'COMPOUND' not in msg:
            return True, "Planning triggered"
        if 'COMPOUND' in msg:
            return False, "Got COMPOUND instead of planning-only"
        return False, "Planning not triggered"

    if expected_skill is None:
        if msg == "":
            return True, "No trigger (expected)"
        return False, f"Unexpected trigger: {msg[:50]}..."

    return False, "Unknown expectation"


class E2ETestSuite:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

    def test(self, name: str, prompt: str, expected_skill: str = None, expected_compound: bool = False, is_warning: bool = False):
        """Run a single test."""
        result = run_hook(prompt)
        passed, reason = check_triggers(result, expected_skill, expected_compound)

        if passed:
            self.passed += 1
            status = f"{GREEN}PASS{RESET}"
        elif is_warning:
            self.warnings += 1
            status = f"{YELLOW}WARN{RESET}"
        else:
            self.failed += 1
            status = f"{RED}FAIL{RESET}"

        self.results.append({
            'name': name,
            'prompt': prompt,
            'passed': passed,
            'reason': reason,
            'is_warning': is_warning
        })

        print(f"  [{status}] {name}")
        if not passed:
            print(f"         Prompt: \"{prompt[:50]}{'...' if len(prompt) > 50 else ''}\"")
            print(f"         Reason: {reason}")

    def section(self, title: str):
        print(f"\n{BOLD}{BLUE}=== {title} ==={RESET}")


def main():
    suite = E2ETestSuite()

    print(f"\n{BOLD}{'='*60}")
    print("COMPREHENSIVE E2E TEST SUITE - user-prompt-submit.py")
    print(f"{'='*60}{RESET}")

    # =========================================================================
    # SECTION 1: Research Keywords (37 keywords)
    # =========================================================================
    suite.section("1. RESEARCH KEYWORDS")

    research_keywords = [
        "search", "find", "find out", "look up", "look into", "discover", "uncover",
        "research", "investigate", "analyze", "study", "explore", "examine", "survey",
        "assess", "evaluate", "review", "inspect", "probe", "scrutinize",
        "gather", "collect", "compile",
        "learn about", "tell me about", "dig into", "delve into",
        "what are the latest", "comprehensive", "deep dive", "thorough investigation",
        "in-depth", "detailed overview", "landscape of", "state of the art", "best practices"
    ]

    for kw in research_keywords:
        # Create a prompt that uses the keyword as an action
        prompt = f"{kw.capitalize()} the market trends" if not kw.startswith("what") else f"{kw} trends"
        suite.test(f"Research keyword: '{kw}'", prompt, expected_skill='research')

    # =========================================================================
    # SECTION 2: Planning Keywords (98 keywords)
    # =========================================================================
    suite.section("2. PLANNING KEYWORDS")

    planning_keywords = [
        "plan", "design", "architect", "blueprint", "outline", "draft", "sketch",
        "map out", "structure", "organize", "prototype", "model", "define", "specify",
        "scaffold", "frame", "conceptualize",
        "build", "create", "develop", "implement", "construct", "craft", "engineer",
        "make", "set up", "establish",
        "specs", "specifications", "requirements", "functional requirements",
        "non-functional requirements", "acceptance criteria", "user stories", "use cases",
        "scenarios", "test cases",
        "architecture", "system design", "technical design", "infrastructure",
        "framework", "schema", "data model", "API design", "component design",
        "analyze requirements", "gather requirements", "define requirements",
        "requirement analysis", "feasibility study", "needs assessment", "scope definition",
        "PRD", "product requirements document", "technical spec", "design doc",
        "architecture document", "ADR", "architecture decision record", "RFC", "proposal",
        "features", "feature list", "capabilities", "functionality", "feature set",
        "feature spec", "MVP", "minimum viable product",
        "roadmap", "project plan", "implementation plan", "development plan",
        "rollout plan", "migration plan", "deployment plan"
    ]

    # Special handling for keywords that might conflict with research keywords
    special_prompts = {
        'architect': "I need to architect the system design",  # Uses intent pattern
        'feasibility study': "Prepare a feasibility study document for the project",  # Document type
    }

    # Keywords that legitimately trigger compound (contain research action verbs)
    compound_keywords = {'analyze requirements'}  # "analyze" is research action

    for kw in planning_keywords:
        if kw in compound_keywords:
            # These trigger compound detection - that's correct behavior
            prompt = f"Need to {kw} for the new app"
            suite.test(f"Planning keyword: '{kw}' (compound)", prompt, expected_compound=True)
        elif kw in special_prompts:
            prompt = special_prompts[kw]
            suite.test(f"Planning keyword: '{kw}'", prompt, expected_skill='planning')
        elif len(kw.split()) == 1:
            prompt = f"{kw.capitalize()} the new application"
            suite.test(f"Planning keyword: '{kw}'", prompt, expected_skill='planning')
        else:
            prompt = f"Need {kw} for the new app"
            suite.test(f"Planning keyword: '{kw}'", prompt, expected_skill='planning')

    # =========================================================================
    # SECTION 3: Verb Form Tests (KNOWN LIMITATION)
    # =========================================================================
    suite.section("3. VERB FORMS (known limitation - word boundary)")

    # Verb forms like "researching", "building" don't match word boundary regex
    # This is BY DESIGN to prevent false positives like "researcher" triggering "research"
    # Users should use base forms or intent patterns will catch these
    print("  INFO: Verb forms (-ing) don't trigger due to word boundary matching")
    print("        This prevents false positives like 'researcher' triggering 'research'")
    print("        Intent patterns may catch some verb form usages")
    print("")

    # Verify that verb forms DON'T trigger (expected behavior)
    verb_form_tests = [
        ("researching the market", None, "Verb: researching → No trigger (expected)"),
        ("building an application", None, "Verb: building → No trigger (expected)"),
        ("investigating the issue", None, "Verb: investigating → No trigger (expected)"),
        ("designing the system", None, "Verb: designing → No trigger (expected)"),
    ]

    for prompt, expected, name in verb_form_tests:
        suite.test(name, prompt, expected_skill=expected)

    # =========================================================================
    # SECTION 4: Intent Pattern Tests
    # =========================================================================
    suite.section("4. INTENT PATTERNS")

    intent_tests = [
        ("Search for API documentation", "research", "Pattern: search for"),
        ("Research notification systems for mobile", "research", "Pattern: research X for"),
        ("Comprehensive analysis of competitors", "research", "Pattern: comprehensive analysis"),
        ("Deep dive into the codebase", "research", "Pattern: deep dive into"),
        ("Build a web application", "planning", "Pattern: build a application"),
        ("Design a system for user management", "planning", "Pattern: design a system"),
        ("What should we build next?", "planning", "Pattern: what should we build"),
        ("Help me plan the architecture", "planning", "Pattern: help me plan"),
    ]

    for prompt, expected, name in intent_tests:
        suite.test(name, prompt, expected_skill=expected)

    # =========================================================================
    # SECTION 5: Compound Detection Tests
    # =========================================================================
    suite.section("5. COMPOUND DETECTION")

    # TRUE compounds - should ask user
    suite.test("TRUE compound: research AND build",
               "Research notification systems and build it",
               expected_compound=True)
    suite.test("TRUE compound: investigate THEN create",
               "Investigate APIs then create implementation",
               expected_compound=True)
    suite.test("TRUE compound: analyze AND design",
               "Analyze the requirements and design the system",
               expected_compound=True)

    # FALSE compounds - should route to single skill
    suite.test("FALSE compound: Build search feature",
               "Build a search feature",
               expected_skill='planning')
    suite.test("FALSE compound: Research build tools",
               "Research build tools",
               expected_skill='research')
    suite.test("FALSE compound: Create analysis dashboard",
               "Create an analysis dashboard",
               expected_skill='planning')

    # =========================================================================
    # SECTION 6: Negation Handling
    # =========================================================================
    suite.section("6. NEGATION HANDLING")

    suite.test("Negation: Don't research",
               "Don't research, just build it",
               expected_skill='planning')
    suite.test("Negation: Skip planning",
               "Skip the planning, just research it",
               expected_skill='research')
    suite.test("Negation: No need to research",
               "No need to research, build the feature",
               expected_skill='planning')

    # =========================================================================
    # SECTION 7: Word Boundary Tests
    # =========================================================================
    suite.section("7. WORD BOUNDARY (preventing false positives)")

    suite.test("Word boundary: researcher",
               "Hire a researcher",
               expected_skill=None)
    suite.test("Word boundary: builder",
               "The builder is excellent",
               expected_skill=None)
    suite.test("Word boundary: searcher",
               "The searcher found nothing",
               expected_skill=None)
    suite.test("Word boundary: planner",
               "Talk to the planner",
               expected_skill=None)
    suite.test("Word boundary: designers",
               "The designers are busy",
               expected_skill=None)

    # =========================================================================
    # SECTION 8: Compound Noun Detection
    # =========================================================================
    suite.section("8. COMPOUND NOUN DETECTION")

    suite.test("Compound noun: search and analysis tool",
               "Build a search and analysis tool",
               expected_skill='planning')
    suite.test("Compound noun: research and development",
               "Create a research and development system",
               expected_skill='planning')

    # =========================================================================
    # SECTION 9: Edge Cases
    # =========================================================================
    suite.section("9. EDGE CASES")

    suite.test("Edge: Empty prompt", "", expected_skill=None)
    suite.test("Edge: Very short", "Hi", expected_skill=None)
    suite.test("Edge: Punctuation only", "!@#$%", expected_skill=None)
    suite.test("Edge: Hello", "Hello there", expected_skill=None)
    suite.test("Edge: Simple question", "What time is it?", expected_skill=None)
    suite.test("Edge: Unicode", "研究 this topic", expected_skill=None)  # Chinese for "research"
    suite.test("Edge: Numbers", "12345 67890", expected_skill=None)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print(f"\n{BOLD}{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}{RESET}")

    total = suite.passed + suite.failed + suite.warnings
    print(f"\n  Total tests: {total}")
    print(f"  {GREEN}Passed: {suite.passed}{RESET}")
    print(f"  {RED}Failed: {suite.failed}{RESET}")
    print(f"  {YELLOW}Warnings: {suite.warnings}{RESET} (potential regressions to review)")

    pass_rate = (suite.passed / total * 100) if total > 0 else 0
    print(f"\n  Pass rate: {pass_rate:.1f}%")

    if suite.failed > 0:
        print(f"\n{RED}{BOLD}FAILED TESTS:{RESET}")
        for r in suite.results:
            if not r['passed'] and not r['is_warning']:
                print(f"  - {r['name']}: {r['reason']}")

    if suite.warnings > 0:
        print(f"\n{YELLOW}{BOLD}WARNINGS (review needed):{RESET}")
        for r in suite.results:
            if not r['passed'] and r['is_warning']:
                print(f"  - {r['name']}: {r['reason']}")

    print()

    # Return exit code
    if suite.failed > 0:
        print(f"{RED}Some tests FAILED. Review and fix before merge.{RESET}")
        return 1
    elif suite.warnings > 0:
        print(f"{YELLOW}All tests passed but {suite.warnings} warnings need review.{RESET}")
        return 0
    else:
        print(f"{GREEN}All tests PASSED! Ready to merge.{RESET}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
