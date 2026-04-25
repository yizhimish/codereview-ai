/**
 * Code Review AI - Test Suite
 * 
 * Run: node test.js
 */

const { analyze } = require('./lib/analyzer');

console.log('🧪 Running Code Review AI Tests\n');

// Test 1: Python code
const pythonCode = `
def calculate_sum(n):
    result = []
    for i in range(n):
        result.append(i * 2)
    return result

print(calculate_sum(10))
`;

console.log('Test 1: Python Code Analysis');
console.log('-'.repeat(40));
const result1 = analyze(pythonCode, 'python');
console.log('Quality Score:', result1.quality_score);
console.log('Issues Found:', result1.issues.length);
result1.issues.forEach((issue, idx) => {
  console.log(`  ${idx + 1}. [${issue.type}] Line ${issue.line}: ${issue.message}`);
});
console.log('');

// Test 2: JavaScript code
const jsCode = `
function processData(data) {
    var result = [];
    for (var i = 0; i < data.length; i++) {
        if (data[i] > 0) {
            result.push(data[i] * 2);
        }
    }
    console.log(result);
    return result;
}

var x = 5 == "5";  // Should flag this
`;

console.log('Test 2: JavaScript Code Analysis');
console.log('-'.repeat(40));
const result2 = analyze(jsCode, 'javascript');
console.log('Quality Score:', result2.quality_score);
console.log('Issues Found:', result2.issues.length);
result2.issues.forEach((issue, idx) => {
  console.log(`  ${idx + 1}. [${issue.type}] Line ${issue.line}: ${issue.message}`);
});
console.log('');

// Test 3: Clean code
const cleanCode = `
def get_squared_numbers(numbers):
    return [x ** 2 for x in numbers if x > 0]
`;

console.log('Test 3: Clean Code (should have no issues)');
console.log('-'.repeat(40));
const result3 = analyze(cleanCode, 'python');
console.log('Quality Score:', result3.quality_score);
console.log('Issues Found:', result3.issues.length);
console.log('');

console.log('✅ All tests completed!');