#!/bin/bash

# UAP GitHub Repository Setup Script
# This script helps set up the UAP project for GitHub contribution

set -e

echo "🚀 Setting up UAP for GitHub contribution..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run 'git init' first."
    exit 1
fi

# Check if remote origin exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  No remote origin found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/your-username/uap.git"
    echo ""
    read -p "Press Enter to continue after adding the remote..."
fi

# Install pre-commit hooks
echo "📝 Installing pre-commit hooks..."
if command -v poetry >/dev/null 2>&1; then
    poetry run pre-commit install
else
    echo "⚠️  Poetry not found. Please install pre-commit manually:"
    echo "   pip install pre-commit"
    echo "   pre-commit install"
fi

# Create initial commit if needed
if [ -z "$(git log --oneline 2>/dev/null)" ]; then
    echo "📦 Creating initial commit..."
    git add .
    git commit -m "feat: initial UAP implementation

- Complete three-layer architecture (Contextual Kernel, AML, Reflexion Loop)
- Protocol bridge adapters (MCP, A2A, ACP)
- Comprehensive error handling and observability
- Full test suite with 80%+ coverage
- Production-ready documentation and deployment guides"
fi

# Set up branch protection (requires GitHub CLI)
if command -v gh >/dev/null 2>&1; then
    echo "🔒 Setting up branch protection..."
    gh api repos/:owner/:repo/branches/main/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["test","lint","type-check"]}' \
        --field enforce_admins=true \
        --field required_pull_request_reviews='{"required_approving_review_count":2}' \
        --field restrictions=null \
        --field allow_force_pushes=false \
        --field allow_deletions=false \
        --field required_conversation_resolution=true \
        || echo "⚠️  Could not set up branch protection. Please configure manually in GitHub settings."
else
    echo "⚠️  GitHub CLI not found. Please set up branch protection manually:"
    echo "   1. Go to GitHub repository settings"
    echo "   2. Navigate to Branches"
    echo "   3. Add rule for 'main' branch"
    echo "   4. Enable required status checks, reviews, and conversation resolution"
fi

# Create initial release
if command -v gh >/dev/null 2>&1; then
    echo "🏷️  Creating initial release..."
    gh release create v1.0.0 \
        --title "UAP v1.0.0 - Initial Release" \
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
- [Community Discussions](https://github.com/your-org/uap/discussions)" \
        --draft \
        || echo "⚠️  Could not create release. Please create manually in GitHub."
else
    echo "⚠️  GitHub CLI not found. Please create initial release manually:"
    echo "   1. Go to GitHub repository releases"
    echo "   2. Create new release with tag v1.0.0"
    echo "   3. Use the release notes from .github/RELEASE_TEMPLATE.md"
fi

# Set up repository settings
if command -v gh >/dev/null 2>&1; then
    echo "⚙️  Configuring repository settings..."
    gh api repos/:owner/:repo \
        --method PATCH \
        --field has_issues=true \
        --field has_projects=true \
        --field has_wiki=false \
        --field has_downloads=true \
        --field allow_squash_merge=true \
        --field allow_merge_commit=false \
        --field allow_rebase_merge=true \
        --field delete_branch_on_merge=true \
        --field allow_auto_merge=true \
        --field allow_update_branch=true \
        || echo "⚠️  Could not update repository settings. Please configure manually."
fi

# Enable GitHub Pages (if needed)
if command -v gh >/dev/null 2>&1; then
    echo "📄 Setting up GitHub Pages..."
    gh api repos/:owner/:repo/pages \
        --method POST \
        --field source='{"branch":"gh-pages","path":"/docs"}' \
        || echo "⚠️  Could not set up GitHub Pages. Please configure manually if needed."
fi

# Create development branch
echo "🌿 Creating development branch..."
git checkout -b develop || echo "⚠️  Develop branch already exists."
git push -u origin develop || echo "⚠️  Could not push develop branch."

# Return to main branch
git checkout main

echo ""
echo "✅ GitHub setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Review and update the following files:"
echo "      - .github/CODEOWNERS (update maintainer usernames)"
echo "      - .github/dependabot.yml (update maintainer usernames)"
echo "      - README.md (update repository URLs)"
echo "      - CONTRIBUTING.md (update contact information)"
echo "      - SECURITY.md (update security contact)"
echo ""
echo "   2. Configure GitHub repository settings:"
echo "      - Enable Issues and Projects"
echo "      - Set up branch protection rules"
echo "      - Configure required status checks"
echo "      - Set up code owners"
echo ""
echo "   3. Set up CI/CD secrets:"
echo "      - DOCKER_USERNAME"
echo "      - DOCKER_PASSWORD"
echo "      - CODECOV_TOKEN (if using Codecov)"
echo ""
echo "   4. Create initial release:"
echo "      - Go to GitHub repository releases"
echo "      - Create release with tag v1.0.0"
echo "      - Use release notes from .github/RELEASE_TEMPLATE.md"
echo ""
echo "   5. Set up monitoring and alerts:"
echo "      - Configure repository notifications"
echo "      - Set up dependency alerts"
echo "      - Configure security alerts"
echo ""
echo "🎉 Your UAP project is now ready for GitHub contribution!"
