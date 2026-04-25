#!/usr/bin/env node

const { program } = require('commander');
const chalk = require('chalk');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const API_URL = 'http://localhost:9000';

program
  .name('code-review')
  .description('AI-Powered Code Review CLI')
  .version('1.0.0');

program
  .command('review')
  .description('Review code using AI')
  .option('-f, --file <path>', 'Path to code file')
  .option('-l, --language <lang>', 'Programming language', 'auto')
  .option('-c, --code <code>', 'Code to review (inline)')
  .action(async (options) => {
    try {
      let code = '';
      
      if (options.file) {
        if (!fs.existsSync(options.file)) {
          console.error(chalk.red(`File not found: ${options.file}`));
          process.exit(1);
        }
        code = fs.readFileSync(options.file, 'utf8');
      } else if (options.code) {
        code = options.code;
      } else {
        console.error(chalk.red('Please provide --file or --code'));
        process.exit(1);
      }

      const language = options.language === 'auto' ? detectLanguage(code) : options.language;
      
      console.log(chalk.blue('Analyzing code with AI...'));
      
      const response = await axios.post(`${API_URL}/analyze`, {
        code: code,
        language: language
      });

      const result = response.data;
      
      console.log(chalk.green('\n✅ Code Review Complete\n'));
      console.log(chalk.bold('Quality Score: '), getScoreColor(result.quality_score || 0) + '/100');
      console.log(chalk.bold('\nIssues Found:'), result.issues?.length || 0);
      
      if (result.issues && result.issues.length > 0) {
        console.log(chalk.bold('\n📋 Detailed Issues:\n'));
        result.issues.forEach((issue, idx) => {
          console.log(`${idx + 1}. ${chalk.yellow(issue.type)} - Line ${issue.line || 'N/A'}`);
          console.log(`   ${issue.message}`);
          if (issue.suggestion) {
            console.log(`   ${chalk.green('→')} ${issue.suggestion}`);
          }
          console.log('');
        });
      }
      
      if (result.summary) {
        console.log(chalk.bold('Summary:'), result.summary);
      }

    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      console.log(chalk.yellow('\nMake sure the CodeReview AI server is running on localhost:9000'));
      console.log(chalk.yellow('Start it with: node main_fixed_v2.py'));
    }
  });

program
  .command('check')
  .description('Check server health')
  .action(async () => {
    try {
      const response = await axios.get(`${API_URL}/health`);
      console.log(chalk.green('✅ Server is healthy'));
      console.log(response.data);
    } catch (error) {
      console.error(chalk.red('❌ Server is not reachable'));
      console.log(chalk.yellow('\nStart server with: node main_fixed_v2.py'));
    }
  });

program.parse();

function detectLanguage(code) {
  if (code.includes('def ') || code.includes('import ') && code.includes(':')) return 'python';
  if (code.includes('function') || code.includes('const ') || code.includes('let ')) return 'javascript';
  if (code.includes('public class') || code.includes('public static')) return 'java';
  if (code.includes('func ') && code.includes('package')) return 'go';
  if (code.includes('#include') || code.includes('int main')) return 'cpp';
  return 'auto';
}

function getScoreColor(score) {
  if (score >= 80) return chalk.green(score);
  if (score >= 60) return chalk.yellow(score);
  return chalk.red(score);
}