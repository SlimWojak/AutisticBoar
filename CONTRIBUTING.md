# Contributing to AutistBoar

## Can I Fork This Repository?

**Yes, you can fork this repository on GitHub.**

While AutistBoar is a private project, forking is enabled for:
- **Development and testing** — experiment with changes in isolation
- **Feature contributions** — develop new skills or improvements
- **Bug fixes** — work on fixes before submitting PRs
- **Learning** — study the architecture and trading strategies

### How to Fork

1. **Via GitHub Web:**
   - Click the "Fork" button at the top-right of the repository page
   - Choose your account or organization as the destination
   - The fork will be created as a private repository in your account

2. **Via GitHub CLI:**
   ```bash
   gh repo fork SlimWojak/AutisticBoar --clone
   ```

### Working with Your Fork

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/AutisticBoar.git
cd AutisticBoar

# Add upstream remote to sync with main repo
git remote add upstream https://github.com/SlimWojak/AutisticBoar.git

# Keep your fork up to date
git fetch upstream
git merge upstream/main
```

## Development Guidelines

### Before You Start

1. **Read the docs:**
   - `BOAR_MANIFEST.md` — system architecture and invariants
   - `AGENTS.md` — operating rules and decision framework
   - `HEARTBEAT.md` — trading cycle logic
   - `docs/BUILD_PLAN_v0.2.md` — implementation details

2. **Set up your environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pytest tests/ -v  # Run tests to verify setup
   ```

3. **Configure your fork:**
   - Copy `.env.example` to `.env`
   - **NEVER commit real API keys or private keys**
   - Use test/development credentials only

### Making Changes

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow the invariants:**
   - **INV-BLIND-KEY**: Never expose or log private keys
   - **INV-RUG-WARDEN-VETO**: Maintain Rug Warden veto power
   - **INV-HUMAN-GATE-100**: Keep human approval gate for large trades
   - See `AGENTS.md` for complete list of invariants

3. **Test your changes:**
   ```bash
   pytest tests/ -v
   python test_week1_fixes.py  # If modifying core logic
   ```

4. **Document your changes:**
   - Update relevant `.md` files if you change behavior
   - Add skill documentation (`SKILL.md`) for new skills
   - Keep code comments minimal but meaningful

### Submitting Changes

1. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request:**
   - Use the GitHub web interface to open a PR from your fork
   - Describe what changed and why
   - Reference any related issues
   - Include test results if applicable

3. **PR Review Process:**
   - PRs will be reviewed for security, correctness, and alignment with AutistBoar's philosophy
   - Changes must not violate any invariants
   - Changes must be minimal and surgical (see `AGENTS.md` code change rules)

## What to Work On

### Good First Contributions
- Bug fixes in existing skills
- Documentation improvements
- Test coverage expansion
- Performance optimizations

### Advanced Contributions
- New trading signal skills (oracle, narrative, whale tracking)
- Risk management improvements
- Edge Bank enhancements (bead recall, pattern recognition)
- API client optimizations

### Areas to Avoid
- **DO NOT** change invariants without discussion
- **DO NOT** weaken security guards
- **DO NOT** bypass the Blind KeyMan architecture
- **DO NOT** introduce marketplace/ClawHub dependencies

## Security

- **Never commit secrets**: Use `.env` for all credentials
- **Report security issues privately**: Contact the maintainer directly (don't open public issues)
- **Respect API rate limits**: Use the configured rate limiters
- **Test with small amounts**: Use test tokens or tiny positions for validation

## Questions?

- Check existing documentation in `/docs`
- Review `AGENTS.md` for architectural decisions
- Look at existing skills in `/skills` for examples
- Open a discussion issue for design questions

## License

This project is private and not for public distribution. Forks are permitted for development and contribution purposes only. Do not redistribute or deploy forks for public use without permission.

---

*"A scout with good senses, sharp memory, and the discipline to walk away. That's the edge."*
