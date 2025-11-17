/**
 * Quality Gate Validators for Research Workflow
 *
 * Implements programmatic validation of workflow compliance with detailed
 * remediation guidance when gates fail.
 *
 * Pattern adapted from: DevFlow (opensource, MIT license)
 * Source: https://github.com/mathewtaylor/devflow
 *
 * Quality Gates:
 * 1. Research Completion: All research notes must exist before synthesis
 * 2. Synthesis Enforcement: report-writer agent must perform synthesis
 */

import { existsSync } from 'fs';
import { resolve } from 'path';
import type { ResearchSession } from '../utils/state-manager';

export interface GateResult {
  passed: boolean;
  gate: string;
  reason?: string;
  missingFiles?: string[];
  violation?: boolean;
  remediation?: string;
}

/**
 * Validate synthesis quality gate
 *
 * Checks:
 * 1. All research notes exist
 * 2. Synthesis performed by report-writer agent (not orchestrator)
 * 3. Synthesis report file exists
 *
 * @param state Current research session state
 * @returns Gate validation result
 */
export async function validateSynthesisGate(state: ResearchSession): Promise<GateResult> {
  // Gate 1: All research notes must exist
  const requiredNotes = state.phases.decomposition.subtopics?.map(
    topic => resolve(`files/research_notes/${topic}.md`)
  ) || [];

  const existingNotes = requiredNotes.filter(path => existsSync(path));

  if (existingNotes.length !== requiredNotes.length) {
    const missingFiles = requiredNotes
      .filter(path => !existsSync(path))
      .map(path => path.replace(process.cwd(), '.'));

    return {
      passed: false,
      gate: 'research_completion',
      reason: `Not all research notes completed. ${existingNotes.length}/${requiredNotes.length} files found.`,
      missingFiles,
      remediation: 'Ensure all researcher agents have completed and saved their findings before attempting synthesis.'
    };
  }

  // Gate 2: Synthesis must use report-writer agent
  const synthesisPhase = state.phases.synthesis;

  if (synthesisPhase.agent !== 'report-writer') {
    return {
      passed: false,
      gate: 'agent_enforcement',
      reason: `Synthesis performed by "${synthesisPhase.agent}", expected "report-writer"`,
      violation: true,
      remediation: `
**WORKFLOW VIOLATION DETECTED**

The orchestrator attempted to perform synthesis directly instead of delegating
to the report-writer agent.

**Expected Workflow**:
1. Orchestrator verifies all research notes exist
2. Orchestrator spawns report-writer agent via Task tool
3. report-writer agent reads all notes and synthesizes
4. report-writer agent writes comprehensive report
5. Orchestrator reads final report and delivers to user

**What Happened**:
Agent "${synthesisPhase.agent}" performed synthesis (should be "report-writer")

**How to Fix**:
Update multi-agent-researcher skill to exclude Write from allowed-tools.
This creates architectural constraint forcing delegation to report-writer agent.

**Current Status**:
If skill v2.0.0+ is active, this should not happen (architectural enforcement).
This violation indicates either:
- Skill was bypassed
- allowed-tools constraint was modified
- Agent detection logic needs improvement
      `.trim()
    };
  }

  // Gate 3: Synthesis report must exist
  if (!synthesisPhase.output || !existsSync(resolve(synthesisPhase.output))) {
    return {
      passed: false,
      gate: 'synthesis_output',
      reason: 'Synthesis report file not found',
      remediation: `Expected synthesis report at: ${synthesisPhase.output || 'files/reports/{topic}_{timestamp}.md'}`
    };
  }

  // All gates passed
  return {
    passed: true,
    gate: 'synthesis_complete',
    reason: 'All synthesis quality gates passed'
  };
}

/**
 * Validate research completion gate
 *
 * Checks that all expected research note files exist
 *
 * @param state Current research session state
 * @returns Gate validation result
 */
export async function validateResearchGate(state: ResearchSession): Promise<GateResult> {
  const requiredNotes = state.phases.decomposition.subtopics?.map(
    topic => resolve(`files/research_notes/${topic}.md`)
  ) || [];

  const existingNotes = requiredNotes.filter(path => existsSync(path));

  if (existingNotes.length !== requiredNotes.length) {
    const missingFiles = requiredNotes
      .filter(path => !existsSync(path))
      .map(path => path.replace(process.cwd(), '.'));

    return {
      passed: false,
      gate: 'research_completion',
      reason: `${existingNotes.length}/${requiredNotes.length} research notes completed`,
      missingFiles,
      remediation: 'Wait for all researcher agents to complete their investigations before proceeding to synthesis.'
    };
  }

  return {
    passed: true,
    gate: 'research_completion',
    reason: `All ${requiredNotes.length} research notes completed successfully`
  };
}

/**
 * Validate all quality gates for a session
 *
 * @param state Current research session state
 * @returns Array of all gate results
 */
export async function validateAllGates(state: ResearchSession): Promise<GateResult[]> {
  const results: GateResult[] = [];

  // Validate research gate if research phase is completed
  if (state.phases.research.status === 'completed') {
    results.push(await validateResearchGate(state));
  }

  // Validate synthesis gate if synthesis phase is completed
  if (state.phases.synthesis.status === 'completed') {
    results.push(await validateSynthesisGate(state));
  }

  return results;
}

/**
 * Get summary of quality gate status
 *
 * @param state Current research session state
 * @returns Human-readable summary
 */
export async function getGateSummary(state: ResearchSession): Promise<string> {
  const results = await validateAllGates(state);

  if (results.length === 0) {
    return 'No quality gates have been reached yet.';
  }

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => r.passed === false).length;

  let summary = `Quality Gates: ${passed} passed, ${failed} failed\n\n`;

  results.forEach(result => {
    const status = result.passed ? '✅ PASSED' : '❌ FAILED';
    summary += `${status}: ${result.gate}\n`;
    if (result.reason) {
      summary += `  Reason: ${result.reason}\n`;
    }
    if (result.missingFiles && result.missingFiles.length > 0) {
      summary += `  Missing files:\n`;
      result.missingFiles.forEach(file => {
        summary += `    - ${file}\n`;
      });
    }
    if (result.violation) {
      summary += `  ⚠️ WORKFLOW VIOLATION DETECTED\n`;
    }
    if (result.remediation) {
      summary += `  Remediation: ${result.remediation}\n`;
    }
    summary += '\n';
  });

  return summary.trim();
}
