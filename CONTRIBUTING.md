# Contributing

Thanks for helping improve the Creative Web Skills Pack. Contributions should be focused, original, reviewable, and useful in production.

## Development workflow

1. Search existing issues and pull requests before starting work.
2. Fork the repository and create a branch from `main`.
3. Use a short branch name such as `fix/mobile-overflow` or `feat/shader-example`.
4. Make one coherent change per pull request.
5. Run the required checks locally.
6. Open a pull request, complete the template, and respond to review feedback.

Do not push directly to `main`. Maintainers squash-merge accepted pull requests after required checks pass and conversations are resolved.

## Required checks

From the repository root:

```bash
npm ci --prefix showcase-apps/asme-hero
npm run build --prefix showcase-apps/asme-hero
node scripts/build-pages-site.mjs
node scripts/validate-repository.mjs
```

On PowerShell, use `npm.cmd` if script execution policy blocks `npm.ps1`.

## Skill contributions

- Keep the frontmatter `name` equal to the skill directory name.
- Write a concise `description` that explains both capability and trigger conditions.
- Preserve the boundary between orchestration, motion, 3D, shaders, rebuilding, and auditing.
- Prefer concrete workflows, decision rules, verification steps, and failure modes over generic advice.
- Update examples and the showcase when a new workflow needs demonstration.

## Showcase contributions

- Use semantic HTML and keyboard-accessible controls.
- Treat mobile, reduced motion, loading, and static fallback as designed variants.
- Avoid unnecessary libraries and remote assets.
- Verify visual changes in a real browser and describe that evidence in the pull request.
- Do not commit generated `.pages-dist`, `dist`, dependency, test-output, or browser-artifact directories.

## Intellectual property and security

Only submit work you have the right to license under this repository's MIT License. Do not copy proprietary source, paid prompt text, copyrighted assets, credentials, personal data, or distinctive protected expression.

Report vulnerabilities privately according to [SECURITY.md](SECURITY.md). Do not disclose exploitable details in a public issue.

By contributing, you agree that your contribution is licensed under the repository's [MIT License](LICENSE) and that you will follow the [Code of Conduct](CODE_OF_CONDUCT.md).

