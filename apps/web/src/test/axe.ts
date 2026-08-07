import axe from 'axe-core';

export async function runAxe(container: HTMLElement) {
  const result = await axe.run(container);
  return result.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    description: violation.description,
    help: violation.help,
    nodes: violation.nodes.map((node) => ({
      html: node.html,
      target: node.target,
      failureSummary: node.failureSummary,
    })),
  }));
}