#!/usr/bin/env python3
"""
Session Start Hook: Auto-Setup, Logging Initialization & Research Session Restoration

This hook runs on every session start and performs:
1. First-time setup (copy settings.template.json, create directories)
2. Session logging initialization
3. Research session restoration (if applicable)

The auto-setup is lightweight and only performs safe operations:
- Copy settings.template.json -> settings.local.json (if missing)
- Create required directories (if missing)
- Show warnings for configuration issues

For custom configuration, run: python3 setup.py

Pattern Source: claude-agent-sdk-demos/research-agent + Claude-Flow
Enhancement: Auto-setup, research context restoration, quality gate status
"""

import json
import shutil
import sys
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

try:
    import state_manager
    import session_logger
    import config_loader
except ImportError as e:
    print(f"⚠️  Failed to import utilities: {e}", file=sys.stderr)
    print("   Run 'python3 setup.py --repair' to fix", file=sys.stderr)
    sys.exit(0)


def get_project_root() -> Path:
    """Get project root directory"""
    # From .claude/hooks/ go up two levels
    return Path(__file__).parent.parent.parent


def check_and_setup_settings() -> bool:
    """Check and setup settings.local.json from template if needed"""
    project_root = get_project_root()
    template_path = project_root / '.claude' / 'settings.template.json'
    local_path = project_root / '.claude' / 'settings.local.json'

    # If local settings exist, we're good
    if local_path.exists():
        return True

    # Check if template exists
    if not template_path.exists():
        print("⚠️  settings.template.json not found", file=sys.stderr)
        print("   Repository may be incomplete", file=sys.stderr)
        return False

    # First time setup - copy template
    try:
        shutil.copy(template_path, local_path)
        print("\n🔧 First-time setup detected")
        print("✅ Created settings.local.json from template\n")
        return True
    except Exception as e:
        print(f"⚠️  Failed to create settings.local.json: {e}", file=sys.stderr)
        return False


def check_and_create_directories() -> None:
    """Ensure all required directories exist (create if missing)"""
    project_root = get_project_root()

    try:
        config = config_loader.load_config()
        paths = config.get('paths', {})

        created = []
        for path_key, path_value in paths.items():
            full_path = project_root / path_value
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                created.append(path_value)

        if created:
            print(f"✅ Created directories: {', '.join(created)}")

    except Exception as e:
        print(f"⚠️  Failed to create directories: {e}", file=sys.stderr)


def check_config() -> bool:
    """Check if config.json exists and is valid"""
    project_root = get_project_root()
    config_path = project_root / '.claude' / 'config.json'

    if not config_path.exists():
        print("ℹ️  config.json not found - using default configuration")
        print("   Run 'python3 setup.py' for custom paths\n")
        return False

    try:
        config_loader.load_config()
        return True
    except Exception as e:
        print(f"⚠️  config.json is invalid: {e}", file=sys.stderr)
        print("   Run 'python3 setup.py --repair' to fix\n", file=sys.stderr)
        return False


def initialize_session_logging():
    """Initialize session logging"""
    try:
        session_id = session_logger.get_session_id()
        session_logger.initialize_session_logs(session_id)
        session_logger.initialize_session_state(session_id)
        print(f"📝 Session logs: logs/{session_id}_{{transcript.txt,tool_calls.jsonl,state.json}}\n")
    except Exception as e:
        print(f"⚠️  Failed to initialize session logs: {e}", file=sys.stderr)
        # Continue without logging


def check_research_session():
    """Check for active research session and build resumption context"""
    try:
        state = state_manager.load_state()
    except Exception:
        return None

    # Check for active research session
    if not state.get('currentResearch'):
        return None

    sessions = state.get('sessions', [])
    session = next((s for s in sessions if s['id'] == state['currentResearch']), None)

    if not session or session.get('status') != 'in_progress':
        return None

    return build_resumption_context(session)


def build_resumption_context(session: dict) -> str:
    """Build resumption context message"""
    start_date = datetime.fromisoformat(session['startedAt'])
    now = datetime.now()
    duration_minutes = int((now - start_date).total_seconds() / 60)

    # Phase status indicators
    def get_phase_status(status):
        return {
            'completed': '✅',
            'in_progress': '⏳',
            'failed': '❌'
        }.get(status, '⏸️')

    # Get next steps based on current phase
    def get_next_steps():
        phases = session['phases']

        if phases['delivery']['status'] in ['in_progress', 'completed']:
            return '- Deliver final report to user\n- Mark session as complete'

        if phases['synthesis']['status'] == 'in_progress':
            return '- Wait for report-writer agent to complete synthesis\n- Read completed report\n- Deliver to user'

        if phases['synthesis']['status'] == 'pending' and phases['research']['status'] == 'completed':
            return '- ⚠️ CRITICAL: Spawn report-writer agent for synthesis\n- Agent will read all research notes\n- Agent will create comprehensive report'

        if phases['research']['status'] == 'in_progress':
            completed = len(phases['research'].get('outputs', []))
            total = phases['research'].get('parallelInstances', 0)
            remaining = max(0, total - completed)
            return f"- Wait for {remaining} remaining researcher agent(s) to complete\n- Monitor files/research_notes/ for new notes\n- Proceed to synthesis when all {total} notes are ready"

        return '- Continue with workflow from current phase'

    # Build file list
    research_files = session['phases']['research'].get('outputs', [])
    synthesis_file = session['phases']['synthesis'].get('output')

    file_list = list(research_files)
    if synthesis_file:
        file_list.append(synthesis_file)

    # Build subtopics list
    subtopics = session['phases']['decomposition'].get('subtopics', [])
    subtopics_str = '\n'.join(f'{i+1}. {topic}' for i, topic in enumerate(subtopics))
    if not subtopics_str:
        subtopics_str = 'None defined'

    # Build file list string
    files_str = '\n'.join(f'- `{f}`' for f in file_list)
    if not files_str:
        files_str = 'No files created yet'

    # Check for quality gate failures
    synthesis_warning = ''
    if session['qualityGates']['synthesis']['status'] == 'failed':
        synthesis_warning = '⚠️ **WARNING**: Synthesis quality gate failed. Check state.json for violation details.\n'

    # Build synthesis agent info
    synthesis_agent = session['phases']['synthesis'].get('agent', 'unknown')
    synthesis_info = f" (by {synthesis_agent})" if synthesis_agent != 'unknown' else ''

    return f"""

## 📋 Research Session Resumed

**Topic**: {session['topic']}
**Session ID**: `{session['id']}`
**Started**: {start_date.strftime('%Y-%m-%d %H:%M:%S')}
**Duration**: {duration_minutes} minutes

### Phase Status

- {get_phase_status(session['phases']['decomposition']['status'])} **Decomposition**: {len(subtopics)} subtopics identified
- {get_phase_status(session['phases']['research']['status'])} **Research**: {len(research_files)}/{session['phases']['research'].get('parallelInstances', 0)} notes completed
- {get_phase_status(session['phases']['synthesis']['status'])} **Synthesis**: {session['phases']['synthesis']['status']}{synthesis_info}
- {get_phase_status(session['phases']['delivery']['status'])} **Delivery**: {session['phases']['delivery']['status']}

### Quality Gates

- **Research Completion**: {session['qualityGates']['research']['status']}{'⚠️' if session['qualityGates']['research']['status'] == 'failed' else ''}
- **Synthesis Enforcement**: {session['qualityGates']['synthesis']['status']}{'⚠️' if session['qualityGates']['synthesis']['status'] == 'failed' else ''}

{synthesis_warning}### Subtopics

{subtopics_str}

### Available Files

{files_str}

### Next Steps

{get_next_steps()}

### State File Location

Full session details available at: `logs/state/research-workflow-state.json`

---

**Note**: Session restoration is active. Continue from the phase indicated above.
""".strip()


def read_prerequisites_state() -> bool:
    """Read semantic-search prerequisites state (fast - just file read)

    Returns:
        True if prerequisites ready, False otherwise
    """
    try:
        project_root = get_project_root()
        state_file = project_root / 'logs' / 'state' / 'semantic-search-prerequisites.json'

        if not state_file.exists():
            return False

        with open(state_file, 'r') as f:
            state = json.load(f)

        return state.get('SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY', False)
    except Exception:
        return False


def get_project_storage_dir(project_path: Path) -> Path:
    """Get project-specific storage directory (matches Python implementation)"""
    storage_dir = Path.home() / '.claude_code_search'
    project_name = project_path.name
    project_hash = hashlib.md5(str(project_path).encode()).hexdigest()[:8]
    return storage_dir / "projects" / f"{project_name}_{project_hash}"


def check_index_exists(project_path: Path) -> bool:
    """Check if semantic search index exists for project"""
    try:
        index_dir = get_project_storage_dir(project_path) / "index"
        return (index_dir / "code.index").exists()
    except Exception:
        return False


def get_index_state_file(project_path: Path) -> Path:
    """Get index state file path"""
    return get_project_storage_dir(project_path) / "index_state.json"


def get_last_full_index_time(project_path: Path) -> datetime:
    """Get timestamp of last full index

    Returns:
        datetime of last full index, or None if never indexed
    """
    try:
        state_file = get_index_state_file(project_path)

        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            state = json.load(f)

        last_full = state.get('last_full_index')
        if last_full:
            return datetime.fromisoformat(last_full)

        return None
    except Exception:
        return None


def run_incremental_reindex_sync(project_path: Path) -> bool:
    """Run incremental reindex synchronously (simple, fast, visible errors)

    This runs within the hook's 60-second timeout.
    Typical duration: ~5 seconds for incremental updates.

    Args:
        project_path: Path to project

    Returns:
        True if successful, False if failed
    """
    try:
        project_root = get_project_root()
        script = project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'incremental-reindex'

        # Run synchronously with timeout (leave 10s buffer from 60s limit)
        result = subprocess.run(
            [str(script), str(project_path)],
            timeout=50,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True
        else:
            # Show error (not suppressed!)
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"⚠️  Index update failed: {error_msg[:300]}\n", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"⚠️  Index update timed out (will retry next session)\n", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  Index update error: {e}\n", file=sys.stderr)
        return False


def auto_reindex_on_session_start(input_data: dict):
    """Auto-reindex with simple synchronous execution

    Simple Business Logic:
    1. Prerequisites FALSE → Skip (manual setup not done yet)
    2. Trigger is 'clear' or 'compact' → Skip (no code changes)
    3. Trigger is 'startup' or 'resume' + no index → Skip with message (manual setup required)
    4. Trigger is 'startup' or 'resume' + index exists → Run incremental synchronously (~5s)

    Design:
    - Synchronous execution (no background processes, no Bug #1481)
    - Fast: ~5 seconds typical for incremental updates
    - Visible errors: Output not suppressed
    - Within timeout: 50s limit, well under 60s hook timeout
    - Simple: No lock files, no daemon, no complexity

    Args:
        input_data: Hook input containing trigger source
    """
    try:
        # Step 1: Check prerequisites (fast - just read state file)
        if not read_prerequisites_state():
            # Prerequisites not ready → skip indexing (manual setup not done)
            return

        # Step 2: Check trigger source
        source = input_data.get('source', 'unknown')

        if source in ['clear', 'compact']:
            # No code changes → skip indexing
            return

        # Step 3: Only auto-index on startup/resume
        if source not in ['startup', 'resume']:
            return

        # Step 4: Check if index exists (require manual first-time setup)
        project_path = get_project_root()

        if not check_index_exists(project_path):
            # No index yet → user needs to run manual setup
            print("ℹ️  Semantic search not yet indexed")
            print("   Run: .claude/skills/semantic-search/scripts/index <project_path> --full")
            print("   (First-time setup: ~3 minutes)\n")
            return

        # Step 5: Run incremental reindex synchronously (~5 seconds)
        print("🔄 Updating semantic search index...")
        success = run_incremental_reindex_sync(project_path)

        if success:
            print("✅ Semantic search index updated\n")
        # Errors already printed by run_incremental_reindex_sync

    except Exception as e:
        # Don't fail hook if auto-indexing fails
        print(f"⚠️  Auto-indexing error: {e}\n", file=sys.stderr)


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Step 1: Auto-setup (first-time only operations)
    check_and_setup_settings()  # Copy template if needed
    check_config()              # Verify config exists
    check_and_create_directories()  # Create dirs if missing

    # Step 2: Initialize session logging
    initialize_session_logging()

    # Step 2.5: Skill crash recovery (check for orphaned skills)
    try:
        current_skill = state_manager.get_current_skill()
        if current_skill and not current_skill.get('endTime'):
            # Found active skill without end time - likely from crash/abrupt termination
            from datetime import timezone
            timestamp = datetime.now(timezone.utc).isoformat()
            skill_name = current_skill['name']
            invocation = current_skill.get('invocationNumber', 1)
            source = input_data.get('source', 'unknown')

            # End it with CrashRecovery trigger
            ended_skill = state_manager.end_current_skill(timestamp, 'CrashRecovery')

            if ended_skill:
                duration = ended_skill.get('duration', 'unknown')
                print(f"🔧 CRASH RECOVERY: {skill_name} ended (invocation #{invocation}, duration: {duration}, source: {source})")
                print(f"   Previous session did not end cleanly. State recovered.\n")
    except Exception as e:
        # Don't fail entire hook if crash recovery fails
        print(f"⚠️  Skill crash recovery failed: {e}", file=sys.stderr)

    # Step 3: Auto-reindex semantic search (if prerequisites met)
    auto_reindex_on_session_start(input_data)

    # Step 4: Check for active research session
    resumption_context = check_research_session()

    if resumption_context:
        print(resumption_context)

    # Exit successfully
    sys.exit(0)


if __name__ == '__main__':
    main()
