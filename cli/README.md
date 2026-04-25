# Code Review AI CLI

AI-Powered Code Review Command Line Tool - Review code in seconds with AI.

## Installation

```bash
npm install -g code-review-ai
```

## Quick Start

```bash
# Check server status
code-review check

# Review a file
code-review review -f ./your-code.py

# Review with language specified
code-review review -f ./script.js -l javascript

# Review inline code
code-review review -c "def hello(): print('world')"
```

## Features

- ⚡ **Fast** - Get AI-powered code review in seconds
- 🌍 **Multi-language** - Python, JavaScript, Java, Go, C++, etc.
- 🎯 **Intelligent** - Detects bugs, performance issues, and best practices
- 📊 **Quality Score** - Get an objective code quality score

## Requirements

- Node.js >= 18.0.0
- CodeReview AI Server running on localhost:9000

## Start the Server

```bash
cd /path/to/code-review-ai/backend
python main_fixed_v2.py
```

## Commands

### `check`
Check if the CodeReview AI server is running.

```bash
code-review check
```

### `review`
Review code with AI.

```bash
# From file
code-review review -f ./example.py

# Specify language
code-review review -f ./example.js -l javascript

# Inline code
code-review review -c "print('hello')"
```

## Example Output

```
✅ Code Review Complete

Quality Score: 85/100

Issues Found: 2

1. Debug - Line 5
   Debug code found: print() statement
   → Remove print statements in production code

2. Performance - Line 10
   Consider using list comprehension instead of append in loop
   → [expr for item in iterable] is more efficient
```

## Supported Languages

- Python
- JavaScript
- TypeScript
- Java
- Go
- C++
- Ruby
- And more...

## License

MIT - All-AI Company

---

Made with 🔥 by [All-AI Company](https://github.com/all-ai-company)