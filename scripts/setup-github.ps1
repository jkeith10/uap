# UAP GitHub Repository Setup Script (PowerShell)
# This script helps set up the UAP project for GitHub contribution

Write-Host "🚀 Setting up UAP for GitHub contribution..." -ForegroundColor Green

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Not in a git repository. Please run 'git init' first." -ForegroundColor Red
    exit 1
}

# Check if remote origin exists
try {
    $origin = git remote get-url origin 2>$null
    if (-not $origin) {
        Write-Host "⚠️  No remote origin found. Please add your GitHub repository:" -ForegroundColor Yellow
        Write-Host "   git remote add origin https://github.com/your-username/uap.git" -ForegroundColor Cyan
        Write-Host ""
        Read-Host "Press Enter to continue after adding the remote"
    }
} catch {
    Write-Host "⚠️  No remote origin found. Please add your GitHub repository:" -ForegroundColor Yellow
    Write-Host "   git remote add origin https://github.com/your-username/uap.git" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to continue after adding the remote"
}

# Install pre-commit hooks
Write-Host "📝 Installing pre-commit hooks..." -ForegroundColor Blue
try {
    if (Get-Command poetry -ErrorAction SilentlyContinue) {
        poetry run pre-commit install
    } else {
        Write-Host "⚠️  Poetry not found. Please install pre-commit manually:" -ForegroundColor Yellow
        Write-Host "   pip install pre-commit" -ForegroundColor Cyan
        Write-Host "   pre-commit install" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️  Could not install pre-commit hooks. Please install manually." -ForegroundColor Yellow
}

# Create initial commit if needed
$gitLog = git log --oneline 2>$null
if (-not $gitLog) {
    Write-Host "📦 Creating initial commit..." -ForegroundColor Blue
    git add .
    git commit -m "feat: initial UAP implementation

- Complete three-layer architecture (Contextual Kernel, AML, Reflexion Loop)
- Protocol bridge adapters (MCP, A2A, ACP)
- Comprehensive error handling and observability
- Full test suite with 80%+ coverage
- Production-ready documentation and deployment guides"
}

# Set up branch protection (requires GitHub CLI)
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "🔒 Setting up branch protection..." -ForegroundColor Blue
    try {
        gh api repos/:owner/:repo/branches/main/protection `
            --method PUT `
            --field required_status_checks='{"strict":true,"contexts":["test","lint","type-check"]}' `
            --field enforce_admins=true `
            --field required_pull_request_reviews='{"required_approving_review_count":2}' `
            --field restrictions=null `
            --field allow_force_pushes=false `
            --field allow_deletions=false `
            --field required_conversation_resolution=true
    } catch {
        Write-Host "⚠️  Could not set up branch protection. Please configure manually in GitHub settings." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  GitHub CLI not found. Please set up branch protection manually:" -ForegroundColor Yellow
    Write-Host "   1. Go to GitHub repository settings" -ForegroundColor Cyan
    Write-Host "   2. Navigate to Branches" -ForegroundColor Cyan
    Write-Host "   3. Add rule for 'main' branch" -ForegroundColor Cyan
    Write-Host "   4. Enable required status checks, reviews, and conversation resolution" -ForegroundColor Cyan
}

# Create initial release
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "🏷️  Creating initial release..." -ForegroundColor Blue
    try {
        gh release create v1.0.0 `
            --title "UAP v1.0.0 - Initial Release" `
            --notes "🎉 Initial release of the Unified Autonomy Protocol (UAP)

## What's New
- Complete three-layer architecture implementation
- Protocol bridge adapters (MCP, A2A, ACP)
- Comprehensive error handling and observability
- Full test suite with 80%+ coverage
- Production-ready documentation

## Installation
\`\`\`bash
pip install uap
\`\`\`

## Documentation
- [API Reference](https://docs.your-org.com/uap/api)
- [Architecture Guide](https://docs.your-org.com/uap/architecture)
- [Deployment Guide](https://docs.your-org.com/uap/deployment)

## Support
- [GitHub Issues](https://github.com/your-org/uap/issues)
- [Documentation](https://docs.your-org.com/uap)
- [Community Discussions](https://github.com/your-org/uap/discussions)" `
            --draft
    } catch {
        Write-Host "⚠️  Could not create release. Please create manually in GitHub." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  GitHub CLI not found. Please create initial release manually:" -ForegroundColor Yellow
    Write-Host "   1. Go to GitHub repository releases" -ForegroundColor Cyan
    Write-Host "   2. Create new release with tag v1.0.0" -ForegroundColor Cyan
    Write-Host "   3. Use the release notes from .github/RELEASE_TEMPLATE.md" -ForegroundColor Cyan
}

# Set up repository settings
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "⚙️  Configuring repository settings..." -ForegroundColor Blue
    try {
        gh api repos/:owner/:repo `
            --method PATCH `
            --field has_issues=true `
            --field has_projects=true `
            --field has_wiki=false `
            --field has_downloads=true `
            --field allow_squash_merge=true `
            --field allow_merge_commit=false `
            --field allow_rebase_merge=true `
            --field delete_branch_on_merge=true `
            --field allow_auto_merge=true `
            --field allow_update_branch=true
    } catch {
        Write-Host "⚠️  Could not update repository settings. Please configure manually." -ForegroundColor Yellow
    }
}

# Create development branch
Write-Host "🌿 Creating development branch..." -ForegroundColor Blue
try {
    git checkout -b develop
} catch {
    Write-Host "⚠️  Develop branch already exists." -ForegroundColor Yellow
}

try {
    git push -u origin develop
} catch {
    Write-Host "⚠️  Could not push develop branch." -ForegroundColor Yellow
}

# Return to main branch
git checkout main

Write-Host ""
Write-Host "✅ GitHub setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Review and update the following files:" -ForegroundColor White
Write-Host "      - .github/CODEOWNERS (update maintainer usernames)" -ForegroundColor Gray
Write-Host "      - .github/dependabot.yml (update maintainer usernames)" -ForegroundColor Gray
Write-Host "      - README.md (update repository URLs)" -ForegroundColor Gray
Write-Host "      - CONTRIBUTING.md (update contact information)" -ForegroundColor Gray
Write-Host "      - SECURITY.md (update security contact)" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Configure GitHub repository settings:" -ForegroundColor White
Write-Host "      - Enable Issues and Projects" -ForegroundColor Gray
Write-Host "      - Set up branch protection rules" -ForegroundColor Gray
Write-Host "      - Configure required status checks" -ForegroundColor Gray
Write-Host "      - Set up code owners" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Set up CI/CD secrets:" -ForegroundColor White
Write-Host "      - DOCKER_USERNAME" -ForegroundColor Gray
Write-Host "      - DOCKER_PASSWORD" -ForegroundColor Gray
Write-Host "      - CODECOV_TOKEN (if using Codecov)" -ForegroundColor Gray
Write-Host ""
Write-Host "   4. Create initial release:" -ForegroundColor White
Write-Host "      - Go to GitHub repository releases" -ForegroundColor Gray
Write-Host "      - Create release with tag v1.0.0" -ForegroundColor Gray
Write-Host "      - Use release notes from .github/RELEASE_TEMPLATE.md" -ForegroundColor Gray
Write-Host ""
Write-Host "   5. Set up monitoring and alerts:" -ForegroundColor White
Write-Host "      - Configure repository notifications" -ForegroundColor Gray
Write-Host "      - Set up dependency alerts" -ForegroundColor Gray
Write-Host "      - Configure security alerts" -ForegroundColor Gray
Write-Host ""
Write-Host "🎉 Your UAP project is now ready for GitHub contribution!" -ForegroundColor Green
