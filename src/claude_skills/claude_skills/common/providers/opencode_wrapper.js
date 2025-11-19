#!/usr/bin/env node

/**
 * OpenCode AI SDK Wrapper for Claude SDD Toolkit
 *
 * This wrapper bridges the Python provider with the Node.js OpenCode AI SDK.
 * It receives prompts and configuration via stdin (to avoid CLI argument length limits)
 * and outputs streaming responses as line-delimited JSON to stdout.
 */

import { createOpencodeClient } from '@opencode-ai/sdk/client';
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
  // OpenCode client doesn't need explicit cleanup
  // Just null out the reference
  opcodeClient = null;
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

  // Get server configuration from environment variables
  const serverUrl = process.env.OPENCODE_SERVER_URL || 'https://api.opencode.ai';
  const apiKey = process.env.OPENCODE_API_KEY;

  // Note: OPENCODE_API_KEY is only required for Zen models
  // For non-Zen models (openai/*, anthropic/*, etc.), the SDK uses ~/.local/share/opencode/auth.json

  // Validate configuration object
  if (payload.config && typeof payload.config !== 'object') {
    throw new Error('config must be an object');
  }

  // Create OpenCode client that connects to server
  // Python provider ensures server is running via _ensure_server_running()
  opcodeClient = createOpencodeClient({
    baseUrl: 'http://localhost:4096'
  });

  // Parse model specification
  const modelConfig = payload.config?.model || 'default-model';
  let providerID, modelID;

  // Parse model format: "provider/model" or just "model"
  if (typeof modelConfig === 'string' && modelConfig.includes('/')) {
    [providerID, modelID] = modelConfig.split('/', 2);
  } else if (typeof modelConfig === 'object') {
    providerID = modelConfig.providerID;
    modelID = modelConfig.modelID;
  } else {
    providerID = 'opencode';
    modelID = modelConfig;
  }

  // Create session
  const session = await opcodeClient.session.create();

  try {
    // Build request body, filtering out null/undefined values
    const requestBody = {
      model: {
        providerID: providerID,
        modelID: modelID
      },
      parts: [
        {
          type: 'text',
          text: payload.prompt
        }
      ]
    };

    // Only add system prompt if it's not null/undefined
    if (payload.system_prompt != null) {
      requestBody.system = payload.system_prompt;
    }

    // Execute prompt using the session API with correct structure
    const response = await opcodeClient.session.prompt({
      path: {
        id: session.data.id
      },
      body: requestBody
    });

    // Extract response text from parts
    const responseParts = response.data?.parts || [];
    const textParts = responseParts
      .filter(part => part.type === 'text')
      .map(part => part.text)
      .join('');

    // Emit response as line-delimited JSON
    const finalResponse = {
      type: 'done',
      response: {
        text: textParts,
        usage: response.data?.usage || {},
        model: `${providerID}/${modelID}`,
        sessionId: session.data.id
      }
    };
    console.log(JSON.stringify(finalResponse));

  } catch (error) {
    throw new Error(`Prompt execution failed: ${error.message}`);
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
