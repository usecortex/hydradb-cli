# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in HydraDB CLI, please report it responsibly. **Do not open a public GitHub issue.**

Send an email to **security@hydradb.com** with the following information:

1. A description of the vulnerability
2. Steps to reproduce the issue
3. The potential impact
4. Any suggested fixes (optional but appreciated)

## Response Timeline

- **Acknowledgment:** within 48 hours of your report
- **Initial assessment:** within 5 business days
- **Fix or mitigation:** as soon as reasonably possible, depending on severity

We will coordinate with you on disclosure timing. We ask that you give us reasonable time to address the issue before making it public.

## Scope

This policy covers the HydraDB CLI tool and its source code. It does not cover the HydraDB API service itself -- for API security issues, contact the HydraDB team directly at https://hydradb.com.

### In scope

- Authentication and credential handling (`~/.hydradb/config.json`)
- API key exposure or leakage
- Command injection or path traversal
- Dependency vulnerabilities
- Insecure defaults

### Out of scope

- The HydraDB API service
- Third-party dependencies (report those to the upstream project)
- Social engineering attacks

## Credential Security

HydraDB CLI stores API keys in `~/.hydradb/config.json` with restrictive file permissions (0600). The CLI also supports environment variables (`HYDRA_DB_API_KEY`) as an alternative to file-based storage. API keys are masked in all CLI output.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

We recommend always using the latest release.
