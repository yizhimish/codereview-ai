/**
 * Code Review AI - Library
 * Core analysis functions
 */

function analyze(code, language) {
  const issues = [];
  const lines = code.split('\n');

  // Common patterns
  const patterns = {
    python: {
      consoleLog: /print\s*\(/,
      listComprehension: /\bfor\s+\w+\s+in\s+.*:\s*\n\s+\w+\.append/,
      unusedVariable: /^(\w+)\s*=.*$(?:\n(?!\1\s*=).*)*\n\1\b/,
      tooManyParameters: /def\s+\w+\([^)]{50,}\)/,
      emptyExcept: /except\s*:/
    },
    javascript: {
      consoleLog: /console\.(log|debug)/,
      useLetConst: /\bvar\s+\w+/,
      useEquals: /==(?!=)/,
      emptyCatch: /catch\s*\(\w*\)\s*{}/,
      tooManyReturns: /return\s+[^;]+;\n.{0,50}return/
    }
  };

  // Detect issues
  lines.forEach((line, idx) => {
    // Line length
    if (line.length > 120) {
      issues.push({
        type: 'Style',
        line: idx + 1,
        message: `Line exceeds 120 characters (${line.length})`,
        suggestion: 'Consider breaking this line into multiple lines'
      });
    }

    // Language-specific
    if (language === 'python' || language === 'auto') {
      if (patterns.python.consoleLog.test(line)) {
        issues.push({
          type: 'Debug',
          line: idx + 1,
          message: 'Debug code found: print() statement',
          suggestion: 'Remove print statements in production code'
        });
      }
      if (patterns.python.listComprehension.test(code)) {
        issues.push({
          type: 'Performance',
          line: idx + 1,
          message: 'Consider using list comprehension instead of append in loop',
          suggestion: '[expr for item in iterable] is more efficient'
        });
      }
    }

    if (language === 'javascript' || language === 'auto') {
      if (patterns.javascript.consoleLog.test(line)) {
        issues.push({
          type: 'Debug',
          line: idx + 1,
          message: 'Debug code found: console.log statement',
          suggestion: 'Remove console.log statements in production'
        });
      }
      if (patterns.javascript.useEquals.test(line) && !line.includes('!=')) {
        issues.push({
          type: 'Best Practice',
          line: idx + 1,
          message: 'Use === instead of == for strict comparison',
          suggestion: '=== checks type and value, == only checks value'
        });
      }
    }
  });

  // Calculate quality score
  const baseScore = 100;
  const deduction = issues.length * 5;
  const qualityScore = Math.max(0, baseScore - deduction);

  return {
    quality_score: qualityScore,
    issues: issues,
    summary: `Found ${issues.length} issue(s). Code quality: ${qualityScore}/100`
  };
}

module.exports = { analyze };