#!/usr/bin/env node

/**
 * OpenCode AI SDK Wrapper for Claude SDD Toolkit
 *
 * This wrapper bridges the Python provider with the Node.js OpenCode AI SDK.
 * It receives prompts and configuration via stdin (to avoid CLI argument length limits)
 * and outputs streaming responses as line-delimited JSON to stdout.
 */

import { createOpencode } from '@opencode-ai/sdk';
import { createInterface } from 'readline';

// Global client instance for graceful shutdown
let opcodeClient = null;

/**
 * Parse command line arguments for simple flags
 */
function parseArgs(args) {
  const flags = {
    help: args.includes('--help') || args.includes('-h'),
    version: args.includes('--version') || args.includes('-v'),
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
`);
}

/**
 * Display version information
 */
function showVersion() {
  // Read version from package.json
  import('./package.json', { assert: { type: 'json' } })
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
  if (opcodeClient) {
    try {
      await opcodeClient.close();
      opcodeClient = null;
    } catch (error) {
      console.error('Error closing client:', error.message);
    }
  }
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
      output: process.stdout,
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

  // Get server configuration from environment variables
  const serverUrl = process.env.OPENCODE_SERVER_URL || 'https://api.opencode.ai';
  const apiKey = process.env.OPENCODE_API_KEY;

  if (!apiKey) {
    throw new Error('OPENCODE_API_KEY environment variable is required');
  }

  // Create OpenCode client connection
  opcodeClient = createOpencode({
    apiKey: apiKey,
    baseURL: serverUrl,
    ...payload.config
  });

  // Parse model specification
  const modelConfig = payload.config?.model || 'default-model';
  let providerID, modelID;

  // Parse model format: "provider:model" or just "model"
  if (typeof modelConfig === 'string' && modelConfig.includes(':')) {
    [providerID, modelID] = modelConfig.split(':', 2);
  } else if (typeof modelConfig === 'object') {
    providerID = modelConfig.providerID;
    modelID = modelConfig.modelID;
  } else {
    providerID = 'opencode';
    modelID = modelConfig;
  }

  // Create session
  const session = await opcodeClient.session.create();

  // Execute prompt with model and tool restrictions
  const promptOptions = {
    model: {
      providerID: providerID,
      modelID: modelID
    },
    systemPrompt: payload.system_prompt,
    temperature: payload.config?.temperature,
    maxTokens: payload.config?.max_tokens
  };

  // Add tool restrictions if provided
  if (payload.allowedTools && payload.allowedTools.length > 0) {
    promptOptions.tools = payload.allowedTools;
  }

  // Subscribe to streaming events
  let responseText = '';
  const eventUnsubscribe = opcodeClient.event.subscribe((event) => {
    if (event.type === 'message.delta') {
      // Emit streaming chunk as line-delimited JSON
      const chunk = {
        type: 'chunk',
        content: event.delta.text || event.delta.content || ''
      };
      console.log(JSON.stringify(chunk));
      responseText += chunk.content;
    }
  });

  try {
    // Execute the prompt with streaming
    const response = await session.prompt(payload.prompt, promptOptions);

    // Emit final response with metadata
    const finalResponse = {
      type: 'done',
      response: {
        text: responseText || response.text,
        usage: response.usage,
        sessionId: session.id
      }
    };
    console.log(JSON.stringify(finalResponse));

  } finally {
    // Unsubscribe from events
    if (eventUnsubscribe) {
      eventUnsubscribe();
    }
  }

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
