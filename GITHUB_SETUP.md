# GitHub Setup Guide

This guide will help you set up the UAP project for GitHub contribution.

## Prerequisites

- Git installed and configured
- GitHub account
- GitHub CLI (optional but recommended)
- Poetry or pip for Python dependency management

## Quick Setup

### 1. Initialize Git Repository

```bash
# If not already initialized
git init

# Add remote origin (replace with your repository URL)
git remote add origin https://github.com/your-username/uap.git
```

### 2. Run Setup Script

**For Linux/macOS:**
```bash
./scripts/setup-github.sh
```

**For Windows (PowerShell):**
```powershell
.\scripts\setup-github.ps1
```

### 3. Manual Setup (Alternative)

If the setup script doesn't work, follow these manual steps:

#### Install Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit
# or
poetry install

# Install hooks
pre-commit install
```

#### Create Initial Commit
```bash
git add .
git commit -m "feat: initial UAP implementation

- Complete three-layer architecture (Contextual Kernel, AML, Reflexion Loop)
- Protocol bridge adapters (MCP, A2A, ACP)
- Comprehensive error handling and observability
- Full test suite with 80%+ coverage
- Production-ready documentation and deployment guides"
```

#### Push to GitHub
```bash
git push -u origin main
```

## Repository Configuration

### 1. Update Configuration Files

Edit the following files to match your repository:

- **`.github/CODEOWNERS`** - Update maintainer usernames
- **`.github/dependabot.yml`** - Update maintainer usernames
- **`README.md`** - Update repository URLs
- **`CONTRIBUTING.md`** - Update contact information
- **`SECURITY.md`** - Update security contact

### 2. GitHub Repository Settings

Configure the following in your GitHub repository settings:

#### General Settings
- ✅ Enable Issues
- ✅ Enable Projects
- ❌ Disable Wiki
- ✅ Enable Downloads

#### Merge Settings
- ✅ Allow squash merging
- ❌ Disable merge commits
- ✅ Allow rebase merging
- ✅ Automatically delete head branches
- ✅ Allow auto-merge
- ✅ Allow update branch

#### Branch Protection Rules

Create a branch protection rule for `main`:

- ✅ Require a pull request before merging
- ✅ Require approvals (2 reviewers)
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require review from code owners
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Restrict pushes that create files
- ✅ Include administrators
- ✅ Allow force pushes (disable)
- ✅ Allow deletions (disable)

#### Required Status Checks
- `test` (CI/CD pipeline)
- `lint` (Code linting)
- `type-check` (Type checking)

### 3. CI/CD Secrets

Set up the following secrets in your GitHub repository:

- **`DOCKER_USERNAME`** - Docker Hub username
- **`DOCKER_PASSWORD`** - Docker Hub password/token
- **`CODECOV_TOKEN`** - Codecov token (if using Codecov)

### 4. Create Initial Release

1. Go to GitHub repository releases
2. Create new release with tag `v1.0.0`
3. Use the release notes from `.github/RELEASE_TEMPLATE.md`

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following the style guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Test Changes

```bash
# Run tests
poetry run pytest

# Run linting
poetry run ruff check src/ tests/

# Run type checking
poetry run mypy src/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Issue Templates

The repository includes issue templates for:

- **Bug Reports** - For reporting bugs
- **Feature Requests** - For suggesting new features
- **Questions** - For asking questions

## Pull Request Template

All pull requests will use the template in `.github/pull_request_template.md` which includes:

- Description of changes
- Type of change
- Related issues
- Testing information
- Code quality checklist

## Code Quality

The repository is configured with:

- **Pre-commit hooks** for code quality
- **CI/CD pipeline** for automated testing
- **Dependabot** for dependency updates
- **Code owners** for review requirements

## Security

- **Security policy** in `SECURITY.md`
- **Private vulnerability reporting** enabled
- **Dependency scanning** with Dependabot
- **Code scanning** with GitHub CodeQL

## Monitoring

- **GitHub Actions** for CI/CD
- **Dependabot** for dependency updates
- **Codecov** for coverage reporting
- **GitHub Pages** for documentation

## Support

For help with GitHub setup:

- Check the [GitHub documentation](https://docs.github.com/)
- Review the [Contributing Guidelines](CONTRIBUTING.md)
- Open an issue in the repository
- Contact the maintainers

## Next Steps

After setting up the repository:

1. **Review the configuration** - Make sure all settings are correct
2. **Test the workflow** - Create a test PR to verify everything works
3. **Set up monitoring** - Configure notifications and alerts
4. **Invite contributors** - Add collaborators and code owners
5. **Create documentation** - Set up GitHub Pages if needed

---

**🎉 Your UAP project is now ready for GitHub contribution!**
