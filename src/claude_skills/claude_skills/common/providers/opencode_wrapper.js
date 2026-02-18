#!/usr/bin/env node

/**
 * OpenCode AI SDK Wrapper for Claude SDD Toolkit
 *
 * This wrapper bridges the Python provider with the Node.js OpenCode AI SDK.
 * It receives prompts and configuration via stdin (to avoid CLI argument length limits)
 * and outputs streaming responses as line-delimited JSON to stdout.
 */

import { spawnSync } from 'child_process';
import { createInterface } from 'readline';

/**
 * Parse command line arguments for simple flags
 */
function parseArgs(args) {
  const flags = {
    help: args.includes('--help') || args.includes('-h'),
    version: args.includes('--version') || args.includes('-v'),
    test: args.includes('--test'),
  };
  return flags;
}

/**
 * Display help message
 */
function showHelp() {
  console.log(`
OpenCode AI Wrapper

Usage: node opencode_wrapper.js < input.json

Input Format (JSON via stdin):
{
  "prompt": "User prompt text",
  "system_prompt": "System prompt (optional)",
  "config": {
    "model": "model-name",
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "allowedTools": ["tool1", "tool2"] (optional)
}

Output Format (line-delimited JSON to stdout):
{"type": "chunk", "content": "token"}
{"type": "done", "response": {...}}
{"type": "error", "code": "category", "message": "details"}

Options:
  -h, --help     Show this help message
  -v, --version  Show version information
  --test         Run in test mode (returns mock responses without API key)
`);
}

/**
 * Display version information
 */
function showVersion() {
  // Read version from package.json
  import('./package.json', { with: { type: 'json' } })
    .then(pkg => {
      console.log(`OpenCode Wrapper v${pkg.default.version}`);
      console.log(`@opencode-ai/sdk v${pkg.default.dependencies['@opencode-ai/sdk']}`);
    })
    .catch(() => {
      console.log('OpenCode Wrapper v1.0.0');
    });
}

/**
 * Cleanup function for graceful shutdown
 */
async function cleanup() {
  // No-op for CLI wrapper mode.
}

/**
 * Setup signal handlers for graceful shutdown
 */
function setupSignalHandlers() {
  process.on('SIGINT', async () => {
    await cleanup();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await cleanup();
    process.exit(0);
  });
}

/**
 * Read JSON payload from stdin
 */
async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    const rl = createInterface({
      input: process.stdin,
      terminal: false
    });

    rl.on('line', (line) => {
      data += line;
    });

    rl.on('close', () => {
      try {
        const payload = JSON.parse(data);
        resolve(payload);
      } catch (error) {
        reject(new Error(`Invalid JSON input: ${error.message}`));
      }
    });

    rl.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Main execution function
 */
async function main() {
  // Setup signal handlers for graceful shutdown
  setupSignalHandlers();

  // Parse CLI arguments
  const flags = parseArgs(process.argv.slice(2));

  // Handle simple flags
  if (flags.help) {
    showHelp();
    process.exit(0);
  }

  if (flags.version) {
    showVersion();
    process.exit(0);
  }

  // Read input from stdin
  const payload = await readStdin();

  // Validate required fields
  if (!payload.prompt) {
    throw new Error('Missing required field: prompt');
  }

  // Test mode - return mock response without requiring API key
  if (flags.test) {
    // Simulate streaming chunks
    const mockChunks = ['Mock ', 'response ', 'from ', 'OpenCode ', 'test ', 'mode'];
    for (const chunk of mockChunks) {
      console.log(JSON.stringify({
        type: 'chunk',
        content: chunk
      }));
    }

    // Return mock successful response
    const mockResponse = {
      type: 'done',
      response: {
        text: 'Mock response from OpenCode test mode',
        usage: {
          prompt_tokens: 10,
          completion_tokens: 6,
          total_tokens: 16
        },
        model: 'mock-model',
        sessionId: 'test-session-123'
      }
    };
    console.log(JSON.stringify(mockResponse));
    process.exit(0);
  }

  // Get server configuration from environment variables.
  // Fidelity review uses a local headless server started by the provider.
  const serverUrl = process.env.OPENCODE_SERVER_URL || 'http://127.0.0.1:4097';

  // Validate configuration object
  if (payload.config && typeof payload.config !== 'object') {
    throw new Error('config must be an object');
  }

  // Parse model specification
  const modelConfig = payload.config?.model || 'default-model';
  const selectedModel =
    typeof modelConfig === 'string'
      ? modelConfig
      : `${modelConfig.providerID}/${modelConfig.modelID}`;

  const combinedPrompt = [payload.system_prompt, payload.prompt]
    .filter(value => typeof value === 'string' && value.trim().length > 0)
    .join('\n\n');

  const opencodeBinary = process.env.OPENCODE_CLI_BINARY || 'opencode';
  const commandArgs = [
    'run',
    '--format',
    'json',
    '--model',
    selectedModel,
    '--attach',
    serverUrl,
    combinedPrompt || payload.prompt
  ];

  const completed = spawnSync(opencodeBinary, commandArgs, {
    encoding: 'utf-8',
    env: process.env,
    maxBuffer: 10 * 1024 * 1024
  });

  if (completed.error) {
    throw new Error(`Failed to execute opencode CLI: ${completed.error.message}`);
  }
  if (completed.status !== 0) {
    const stderr = (completed.stderr || '').trim();
    const stdout = (completed.stdout || '').trim();
    throw new Error(
      `opencode run exited with code ${completed.status}: ${stderr || stdout || 'no output'}`
    );
  }

  const lines = (completed.stdout || '')
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean);

  let sessionId = null;
  let collectedText = '';
  let usage = {};
  let streamError = null;

  for (const line of lines) {
    let event;
    try {
      event = JSON.parse(line);
    } catch (error) {
      continue;
    }

    if (event.sessionID) {
      sessionId = event.sessionID;
    }

    if (event.type === 'error') {
      const errorData = event.error || {};
      const errorMessage =
        errorData?.data?.message ||
        errorData?.message ||
        event.message ||
        'Unknown OpenCode error';
      streamError = errorMessage;
    }

    if (event.type === 'text' && event.part && typeof event.part.text === 'string') {
      collectedText += event.part.text;
    }

    if (event.type === 'step_finish' && event.part && event.part.tokens) {
      const tokens = event.part.tokens;
      const inputTokens = Number(tokens.input || 0);
      const outputTokens = Number(tokens.output || 0);
      usage = {
        prompt_tokens: inputTokens,
        completion_tokens: outputTokens,
        total_tokens: inputTokens + outputTokens
      };
    }
  }

  if (streamError) {
    throw new Error(`Prompt execution failed: ${streamError}`);
  }

  const finalResponse = {
    type: 'done',
    response: {
      text: collectedText,
      usage,
      model: selectedModel,
      sessionId: sessionId || null
    }
  };
  console.log(JSON.stringify(finalResponse));

  // Cleanup before exit
  await cleanup();

  // Success - prompt executed and streamed
  process.exit(0);
}

// Run main function if this is the entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    // Structured error output (required by spec)
    const errorResponse = {
      type: 'error',
      code: 'WRAPPER_ERROR',
      message: error.message
    };
    console.log(JSON.stringify(errorResponse));
    process.exit(1);
  });
}

export { readStdin, parseArgs };
